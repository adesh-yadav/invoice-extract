"""Canonical financial result and deterministic controls."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
from datetime import date
import re
from pydantic import BaseModel, Field, field_validator


class Party(BaseModel):
    name: str | None = None
    address: str | None = None
    tax_id: str | None = None
    gstin: str | None = None
    contact: str | None = None


class LineItem(BaseModel):
    description: str | None = None
    quantity: str | None = None
    unit: str | None = None
    unit_price: str | None = None
    discount: str | None = None
    tax_rate: str | None = None
    tax_amount: str | None = None
    hsn_sac: str | None = None
    amount: str | None = None


class Totals(BaseModel):
    subtotal: str | None = None
    discount_total: str | None = None
    shipping: str | None = None
    other_charges: str | None = None
    cgst: str | None = None
    sgst: str | None = None
    igst: str | None = None
    cess: str | None = None
    tax_total: str | None = None
    round_off: str | None = None
    grand_total: str | None = None


class Payment(BaseModel):
    payment_method: str | None = None
    transaction_reference: str | None = None
    amount_paid: str | None = None
    balance_due: str | None = None
    payment_status: str | None = None


class FinancialDocument(BaseModel):
    document_type: str
    document_number: str | None = None
    document_date: str | None = None
    due_date: str | None = None
    currency: str | None = None
    language: str | None = None
    seller: Party = Field(default_factory=Party)
    buyer: Party = Field(default_factory=Party)
    line_items: list[LineItem] = Field(default_factory=list)
    totals: Totals = Field(default_factory=Totals)
    payment: Payment = Field(default_factory=Payment)

    @field_validator("document_type")
    @classmethod
    def valid_type(cls, value: str) -> str:
        if value not in {"invoice", "bill", "receipt"}:
            raise ValueError("Unsupported document type")
        return value


class Evidence(BaseModel):
    field_path: str
    page_number: int
    block_ids: list[str]
    raw_text: str
    resolution: str = "direct_supported_reading"


class ExtractionPayload(BaseModel):
    document: FinancialDocument
    evidence: list[Evidence] = Field(default_factory=list)


class Issue(BaseModel):
    code: str
    severity: str
    field_path: str | None = None
    message: str


def decimal_value(value: str | None) -> Decimal | None:
    if value is None:
        return None
    cleaned = re.sub(r"[₹$,\s]", "", value).replace("Rs.", "").replace("INR", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def normalize(payload: ExtractionPayload) -> tuple[ExtractionPayload, list[Issue]]:
    normalized = payload.model_copy(deep=True)
    issues: list[Issue] = []
    groups = [
        ("document.totals", normalized.document.totals, Totals.model_fields),
        ("document.payment", normalized.document.payment, {"amount_paid": None, "balance_due": None}),
    ]
    for index, item in enumerate(normalized.document.line_items):
        groups.append((f"document.line_items.{index}", item, {name: None for name in ("quantity", "unit_price", "discount", "tax_rate", "tax_amount", "amount")}))
    for prefix, obj, fields in groups:
        for name in fields:
            value = getattr(obj, name)
            if value is None:
                continue
            parsed = decimal_value(value)
            if parsed is None:
                setattr(obj, name, None)
                issues.append(Issue(code="INVALID_DECIMAL", severity="high", field_path=f"{prefix}.{name}", message="Unparseable numeric value"))
            else:
                setattr(obj, name, format(parsed, "f"))
    for name in ("document_date", "due_date"):
        value = getattr(normalized.document, name)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError:
                setattr(normalized.document, name, None)
                issues.append(Issue(code="AMBIGUOUS_DATE", severity="medium", field_path=f"document.{name}", message="Date was not unambiguous ISO format"))
    return normalized, issues


def validate(payload: ExtractionPayload, cdr) -> list[Issue]:
    issues: list[Issue] = []
    doc = payload.document
    valid_blocks = {b.block_id: b.text for p in cdr.pages for b in p.text_blocks}
    block_pages = {b.block_id: p.page_number for p in cdr.pages for b in p.text_blocks}
    if not doc.seller.name:
        issues.append(Issue(code="MISSING_SELLER", severity="high", field_path="document.seller.name", message="Seller or merchant name is missing"))
    if doc.document_type == "invoice" and not doc.document_number:
        issues.append(Issue(code="MISSING_INVOICE_NUMBER", severity="high", field_path="document.document_number", message="Invoice number is missing"))
    for evidence in payload.evidence:
        if evidence.page_number < 1 or any(block_pages.get(block) != evidence.page_number for block in evidence.block_ids):
            issues.append(Issue(code="INVALID_EVIDENCE", severity="high", field_path=evidence.field_path, message="Evidence points outside the source"))
    for field_path, value in (("document.seller.name", doc.seller.name), ("document.document_number", doc.document_number)):
        if not value:
            continue
        citations = [e for e in payload.evidence if e.field_path == field_path and e.block_ids]
        if not citations:
            issues.append(Issue(code="MISSING_FIELD_EVIDENCE", severity="high", field_path=field_path, message="Critical field has no source reference"))
        elif not any(value.casefold() in " ".join(valid_blocks.get(block, "") for block in evidence.block_ids).casefold() for evidence in citations):
            issues.append(Issue(code="FIELD_NOT_IN_SOURCE", severity="high", field_path=field_path, message="Critical field differs from cited text"))
    critical = "document.totals.grand_total"
    total = decimal_value(doc.totals.grand_total)
    if total is None:
        issues.append(Issue(code="MISSING_TOTAL", severity="high", field_path=critical, message="Grand total is missing or invalid"))
    elif not any(e.field_path == critical and e.block_ids for e in payload.evidence):
        issues.append(Issue(code="MISSING_TOTAL_EVIDENCE", severity="high", field_path=critical, message="Grand total has no source reference"))
    else:
        cited = " ".join(valid_blocks.get(block, "") for evidence in payload.evidence if evidence.field_path == critical for block in evidence.block_ids)
        observed_numbers = [decimal_value(value) for value in re.findall(r"\d[\d,]*\.\d+|\d[\d,]*", cited)]
        if total not in observed_numbers:
            issues.append(Issue(code="TOTAL_NOT_IN_SOURCE", severity="high", field_path=critical, message="Grand total differs from cited text"))
    for name in ("document_date", "due_date"):
        value = getattr(doc, name)
        if value:
            try:
                date.fromisoformat(value)
            except ValueError:
                issues.append(Issue(code="INVALID_DATE", severity="medium", field_path=f"document.{name}", message="Date is not ISO formatted"))
    if doc.seller.gstin and not re.fullmatch(r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][A-Z0-9]Z[A-Z0-9]", doc.seller.gstin):
        issues.append(Issue(code="GSTIN_FORMAT", severity="medium", field_path="document.seller.gstin", message="GSTIN format is invalid"))
    subtotal = decimal_value(doc.totals.subtotal)
    tax = decimal_value(doc.totals.tax_total)
    if total is not None and subtotal is not None and tax is not None:
        expected = subtotal - (decimal_value(doc.totals.discount_total) or 0) + tax + (decimal_value(doc.totals.shipping) or 0) + (decimal_value(doc.totals.other_charges) or 0) + (decimal_value(doc.totals.round_off) or 0)
        if abs(expected - total) > Decimal("0.02"):
            issues.append(Issue(code="TOTAL_MISMATCH", severity="high", field_path=critical, message=f"Components sum to {expected}, observed {total}"))
    for index, item in enumerate(doc.line_items):
        quantity, price, amount = (decimal_value(item.quantity), decimal_value(item.unit_price), decimal_value(item.amount))
        if None not in (quantity, price, amount) and abs(quantity * price - amount) > Decimal("0.02") and item.discount is None and item.tax_amount is None:
            issues.append(Issue(code="LINE_ITEM_MISMATCH", severity="medium", field_path=f"document.line_items.{index}.amount", message="Quantity and price do not match amount"))
    return issues
