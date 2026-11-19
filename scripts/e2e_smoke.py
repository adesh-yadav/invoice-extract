"""Run synthetic upload-to-result checks against a locally running API."""
from __future__ import annotations

from io import BytesIO
import json
import time
import uuid

import httpx
import pymupdf
from docx import Document
from PIL import Image, ImageDraw, ImageFont

BASE = "http://localhost:8000"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
TERMINAL = {"completed", "needs_review", "failed", "unsupported"}


def image_bytes(lines: list[str], format: str = "PNG", fill: str = "black") -> bytes:
    image = Image.new("RGB", (1000, 600), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 30)
    for index, line in enumerate(lines):
        draw.text((40, 35 + index * 75), line, fill=fill, font=font)
    output = BytesIO()
    image.save(output, format=format, quality=92)
    return output.getvalue()


def pdf_bytes(lines: list[str], raster: bytes | None = None, mixed: bool = False) -> bytes:
    pdf = pymupdf.open()
    if lines:
        page = pdf.new_page()
        for index, line in enumerate(lines):
            page.insert_text((60, 60 + index * 24), line, fontsize=14)
    if raster is not None:
        page = pdf.new_page()
        page.insert_image(pymupdf.Rect(30, 30, 550, 350), stream=raster)
    data = pdf.tobytes()
    pdf.close()
    return data


def docx_bytes(lines: list[str], embedded: bytes | None = None) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    if embedded is not None:
        doc.add_picture(BytesIO(embedded))
    output = BytesIO()
    doc.save(output)
    return output.getvalue()


def upload(client: httpx.Client, name: str, mime: str, data: bytes) -> httpx.Response:
    return client.post(f"{BASE}/v1/files/upload", files={"file": (name, data, mime)})


def process(client: httpx.Client, file_id: str, job_id: str | None = None) -> dict:
    if job_id is None:
        created = client.post(f"{BASE}/v1/extractions", json={"file_id": file_id})
        assert created.status_code == 202, (created.status_code, created.text[:200])
        job_id = created.json()["job_id"]
    for _ in range(40):
        response = client.get(f"{BASE}/v1/extractions/{job_id}")
        assert response.status_code == 200, (response.status_code, response.text[:200])
        result = response.json()
        if result["status"] in TERMINAL:
            return result
        time.sleep(2)
    raise TimeoutError(job_id)


def main() -> None:
    invoice = ["Acme Supplies", "Tax Invoice", "Invoice Number INV-1001", "Date 2026-11-19", "Buyer Beta Retail", "Notebook INR 100.00", "Total INR 100.00"]
    bill = ["City Utilities", "Bill", "Bill Number BILL-201", "Date 2026-11-19", "Service Fee INR 250.00", "Total INR 250.00"]
    receipt = ["ABC Store", "RECEIPT", "Receipt No R-202", "Date 2026-11-19", "Notebook INR 100.00", "TOTAL INR 100.00"]
    cases = [
        ("invoice_native.pdf", "application/pdf", pdf_bytes(invoice), "invoice", "pdf_native"),
        ("bill_native.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx_bytes(bill), "bill", "docx_native"),
        ("receipt_ocr.png", "image/png", image_bytes(receipt), "receipt", "ocr"),
        ("bill_ocr.jpg", "image/jpeg", image_bytes(bill, "JPEG"), "bill", "ocr"),
        ("invoice_scan.pdf", "application/pdf", pdf_bytes([], image_bytes(invoice)), "invoice", "ocr"),
        ("invoice_mixed.pdf", "application/pdf", pdf_bytes(invoice[:4], image_bytes(invoice[4:]), mixed=True), "invoice", "pdf_native"),
        ("bill_embedded.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", docx_bytes(bill[:2], image_bytes(bill[2:])), "bill", "embedded_image_ocr"),
    ]
    failures = []
    with httpx.Client(timeout=40) as client:
        file_ids = []
        completed_job_id = None
        for name, mime, data, expected_type, expected_method in cases:
            uploaded = upload(client, name, mime, data)
            if uploaded.status_code != 201:
                failures.append(f"{name}: upload HTTP {uploaded.status_code}")
                print(json.dumps({"case": name, "upload_status": uploaded.status_code}), flush=True)
                continue
            file_id = uploaded.json()["id"]
            file_ids.append(file_id)
            if not uploaded.json().get("extraction_job_id") or not uploaded.json().get("extraction_status_url"):
                failures.append(f"{name}: no automatic job")
                continue
            result = process(client, file_id, uploaded.json()["extraction_job_id"])
            document = (result.get("result") or {}).get("document") or {}
            pages = (result.get("source_document") or {}).get("pages") or []
            methods = [method for page in pages for method in page.get("methods", [])]
            actions = [step["action"] for step in result.get("processing_steps") or []]
            summary = {"case": name, "status": result["status"], "document_type": document.get("document_type"), "total": (document.get("totals") or {}).get("grand_total"), "methods": methods, "models_used": result.get("models_used"), "steps": len(actions), "issues": [item["code"] for item in (result.get("validation") or {}).get("issues") or []]}
            print(json.dumps(summary), flush=True)
            if result["status"] != "completed" or document.get("document_type") != expected_type or expected_method not in methods or not result.get("models_used") or not pages or "job_finished" not in actions:
                failures.append(name)
            if result["status"] == "completed":
                completed_job_id = result["job_id"]
            cdr = client.get(f"{BASE}/v1/extractions/{result['job_id']}/cdr")
            if cdr.status_code != 200 or not cdr.json().get("pages"):
                failures.append(f"{name}: CDR")

        unknown = upload(client, "unknown.pdf", "application/pdf", pdf_bytes(["Meeting Notes", "No financial transaction here", "Agenda item one"]))
        assert unknown.status_code == 201
        unknown_result = process(client, unknown.json()["id"], unknown.json().get("extraction_job_id"))
        print(json.dumps({"case": "unknown_document", "status": unknown_result["status"], "error": unknown_result.get("error")}), flush=True)
        if unknown_result["status"] != "needs_review":
            failures.append("unknown_document")
        retry = client.post(f"{BASE}/v1/extractions/{unknown_result['job_id']}/retry")
        print(json.dumps({"case": "retry_review", "http_status": retry.status_code}), flush=True)
        if retry.status_code != 202:
            failures.append("retry_review")

        unsupported = upload(client, "passport.pdf", "application/pdf", pdf_bytes(["Passport Application", "Name Example Person", "Nationality Example"]))
        assert unsupported.status_code == 201
        unsupported_result = process(client, unsupported.json()["id"], unsupported.json().get("extraction_job_id"))
        print(json.dumps({"case": "unsupported_document", "status": unsupported_result["status"]}), flush=True)
        if unsupported_result["status"] != "unsupported":
            failures.append("unsupported_document")

        blank = upload(client, "blank.png", "image/png", image_bytes([]))
        assert blank.status_code == 201
        blank_result = process(client, blank.json()["id"], blank.json().get("extraction_job_id"))
        print(json.dumps({"case": "blank_image", "status": blank_result["status"], "methods": [page.get("methods") for page in (blank_result.get("source_document") or {}).get("pages") or []], "models_used": blank_result.get("models_used")}), flush=True)
        if blank_result["status"] == "completed":
            failures.append("blank_image")

        for name, mime, data, expected in [
            ("old.doc", "application/msword", b"legacy word", 415),
            ("corrupt.png", "image/png", b"not a png", 422),
            ("corrupt.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"not a docx", 422),
            ("empty.png", "image/png", b"", 413),
            ("oversize.png", "image/png", b"x" * (25 * 1024 * 1024 + 1), 413),
        ]:
            response = upload(client, name, mime, data)
            print(json.dumps({"case": name, "http_status": response.status_code}), flush=True)
            if response.status_code != expected:
                failures.append(name)

        secured = pymupdf.open()
        secured.new_page().insert_text((60, 60), "Protected invoice")
        protected = secured.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret")
        secured.close()
        password_response = upload(client, "protected.pdf", "application/pdf", protected)
        print(json.dumps({"case": "password_pdf", "http_status": password_response.status_code}), flush=True)
        if password_response.status_code != 422:
            failures.append("password_pdf")

        missing = client.post(f"{BASE}/v1/extractions", json={"file_id": str(uuid.uuid4())})
        print(json.dumps({"case": "missing_file", "http_status": missing.status_code}), flush=True)
        if missing.status_code != 404:
            failures.append("missing_file")
        if completed_job_id:
            completed_retry = client.post(f"{BASE}/v1/extractions/{completed_job_id}/retry")
            print(json.dumps({"case": "retry_completed", "http_status": completed_retry.status_code}), flush=True)
            if completed_retry.status_code != 409:
                failures.append("retry_completed")

        if len(file_ids) >= 2:
            key = f"e2e-{uuid.uuid4()}"
            first = client.post(f"{BASE}/v1/extractions", json={"file_id": file_ids[0]}, headers={"Idempotency-Key": key})
            same = client.post(f"{BASE}/v1/extractions", json={"file_id": file_ids[0]}, headers={"Idempotency-Key": key})
            conflict = client.post(f"{BASE}/v1/extractions", json={"file_id": file_ids[1]}, headers={"Idempotency-Key": key})
            print(json.dumps({"case": "idempotency", "same_job": first.status_code == same.status_code == 202 and first.json()["job_id"] == same.json()["job_id"], "conflict_status": conflict.status_code}), flush=True)
            if first.status_code != 202 or same.status_code != 202 or first.json()["job_id"] != same.json()["job_id"] or conflict.status_code != 409:
                failures.append("idempotency")

    print(json.dumps({"failed_cases": failures, "passed": not failures}), flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
