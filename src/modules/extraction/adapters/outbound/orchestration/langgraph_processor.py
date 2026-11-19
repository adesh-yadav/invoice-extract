"""Application orchestration; adapters are injected and graph nodes stay small."""
from __future__ import annotations
from pathlib import Path
from typing import TypedDict
import json
import os
from langgraph.graph import StateGraph, START, END
from src.modules.extraction.domain.cdr import CDR, ReaderStatus
from src.modules.extraction.domain.financial import validate, normalize
from src.modules.extraction.application.use_cases.classify import classify
from src.modules.extraction.domain.processing import ProcessingEvent
from src.modules.extraction.application.ports.processing_events import ProcessingEventSink


class WorkflowState(TypedDict, total=False):
    job_id: str
    file_id: str
    file_path: str
    content_type: str
    extension: str
    cdr_ref: str
    reader_status: str
    document_type: str
    payload: dict
    issues: list[dict]
    status: str
    error_code: str
    repair_count: int


class LangGraphProcessor:
    def __init__(self, readers: dict, extractor, artifact_dir: Path, event_sink: ProcessingEventSink | None = None, model_info: dict | None = None):
        self.readers = readers
        self.extractor = extractor
        self.artifact_dir = artifact_dir
        self.event_sink = event_sink
        self.model_info = model_info or {}
        self.graph = self._build_graph()

    def _event(self, state: WorkflowState, phase: str, action: str, status: str = "completed", details: dict | None = None) -> None:
        if self.event_sink is not None:
            self.event_sink.record_event(state["job_id"], ProcessingEvent(phase, action, status, details or {}))

    def _build_graph(self):
        graph = StateGraph(WorkflowState)
        graph.add_node("read", self._read)
        graph.add_node("classify", self._classify)
        graph.add_node("extract", self._extract)
        graph.add_node("validate", self._validate)
        graph.add_node("repair", self._repair)
        graph.add_edge(START, "read")
        graph.add_conditional_edges("read", lambda s: "classify" if s["reader_status"] != "FAILED" else END)
        graph.add_conditional_edges("classify", lambda s: "extract" if s["document_type"] in {"invoice", "bill", "receipt"} else END)
        graph.add_edge("extract", "validate")
        graph.add_conditional_edges("validate", self._after_validation)
        graph.add_edge("repair", "validate")
        return graph.compile()

    def _read(self, state: WorkflowState) -> dict:
        self._event(state, "reading", "document_read", "started", {"file_format": state["extension"].lower()})
        reader = self.readers.get(state["extension"].lower())
        if reader is None:
            self._event(state, "reading", "document_read", "failed", {"error_code": "UNSUPPORTED_FILE_TYPE"})
            return {"reader_status": "FAILED", "status": "failed", "error_code": "UNSUPPORTED_FILE_TYPE"}
        cdr = reader.read(state["file_id"], Path(state["file_path"]), state["content_type"])
        target = self.artifact_dir / state["job_id"]
        target.mkdir(parents=True, exist_ok=True)
        artifact = target / "cdr-v1.json"
        temporary = target / "cdr-v1.tmp"
        temporary.write_text(cdr.model_dump_json(indent=2))
        os.replace(temporary, artifact)
        if self.event_sink is not None:
            self.event_sink.save_cdr(state["job_id"], cdr)
        page_details = [{"page_number": page.page_number, "methods": page.methods, "text_block_count": len(page.text_blocks), "sources": sorted({block.source for block in page.text_blocks}), "warning_codes": [warning.code for warning in page.warnings]} for page in cdr.pages]
        self._event(state, "reading", "document_read", "failed" if cdr.reader_status == ReaderStatus.FAILED else "completed", {"reader": type(reader).__name__, "reader_status": cdr.reader_status.value, "pages": page_details, "warning_codes": [warning.code for warning in cdr.warnings]})
        for page in cdr.pages:
            methods = set(page.methods)
            if methods & {"pdf_native", "docx_native"}:
                self._event(state, "text_reading", "embedded_text_extracted", details={"page_number": page.page_number, "methods": sorted(methods & {"pdf_native", "docx_native"}), "block_count": sum(block.source in {"pdf_native", "docx_native"} for block in page.text_blocks)})
            if methods & {"ocr", "embedded_image_ocr"}:
                self._event(state, "ocr", "text_recognized", details={"page_number": page.page_number, "engine": self.model_info.get("ocr", {"engine": "tesseract"}), "block_count": sum(block.source == "ocr" for block in page.text_blocks)})
            if "vision" in methods:
                self._event(state, "vision", "image_transcribed", details={"page_number": page.page_number, **self.model_info.get("vision", {}), "candidate_block_count": sum(block.source in {"vision", "vision_candidate"} for block in page.text_blocks)})
            if "ocr_cleanup" in methods:
                self._event(state, "ocr_cleanup", "text_corrected", details={"page_number": page.page_number, **self.model_info.get("ocr_cleanup", {}), "candidate_block_count": sum(block.source == "ocr_cleanup_candidate" for block in page.text_blocks)})
        if cdr.reader_status == ReaderStatus.FAILED:
            code = cdr.warnings[0].code if cdr.warnings else "NO_READABLE_CONTENT"
            return {"cdr_ref": str(artifact), "reader_status": "FAILED", "status": "failed", "error_code": code}
        return {"cdr_ref": str(artifact), "reader_status": cdr.reader_status.value}

    def _load_cdr(self, state: WorkflowState) -> CDR:
        return CDR.model_validate_json(Path(state["cdr_ref"]).read_text())

    def _classify(self, state: WorkflowState) -> dict:
        self._event(state, "classification", "document_classified", "started")
        kind = classify(self._load_cdr(state))
        self._event(state, "classification", "document_classified", details={"document_type": kind, "engine": "deterministic_rules"})
        if kind == "unsupported":
            return {"document_type": kind, "status": "unsupported", "error_code": "UNSUPPORTED_DOCUMENT_TYPE"}
        if kind == "unknown":
            return {"document_type": kind, "status": "needs_review", "error_code": "UNKNOWN_DOCUMENT_TYPE"}
        return {"document_type": kind}

    def _extract(self, state: WorkflowState) -> dict:
        if self.extractor is None:
            self._event(state, "extraction", "fields_extracted", "failed", {"error_code": "MODEL_NOT_CONFIGURED", **self.model_info.get("extraction", {})})
            return {"status": "failed", "error_code": "MODEL_NOT_CONFIGURED"}
        self._event(state, "extraction", "fields_extracted", "started", self.model_info.get("extraction", {}))
        try:
            payload = self.extractor.extract(self._load_cdr(state), state["document_type"])
        except Exception as exc:
            self._event(state, "extraction", "fields_extracted", "failed", {"error_type": type(exc).__name__, **self.model_info.get("extraction", {})})
            raise
        self._event(state, "extraction", "fields_extracted", details={"evidence_count": len(payload.evidence), "line_item_count": len(payload.document.line_items), **self.model_info.get("extraction", {})})
        return {"payload": payload.model_dump(mode="json")}

    def _validate(self, state: WorkflowState) -> dict:
        if "payload" not in state:
            return {"status": "failed", "error_code": state.get("error_code", "EXTRACTION_FAILED")}
        from src.modules.extraction.domain.financial import ExtractionPayload
        payload = ExtractionPayload.model_validate(state["payload"])
        payload, normalization_issues = normalize(payload)
        issues = normalization_issues + validate(payload, self._load_cdr(state))
        status = "needs_review" if state["reader_status"] == "PARTIAL" or any(issue.severity == "high" for issue in issues) else "completed"
        self._event(state, "validation", "financial_controls_checked", details={"decision": status, "issue_codes": [issue.code for issue in issues], "engine": "deterministic_rules"})
        return {"payload": payload.model_dump(mode="json"), "issues": [issue.model_dump() for issue in issues], "status": status}

    def _after_validation(self, state: WorkflowState):
        repairable = {"TOTAL_MISMATCH", "TOTAL_NOT_IN_SOURCE", "INVALID_EVIDENCE", "MISSING_FIELD_EVIDENCE", "MISSING_TOTAL_EVIDENCE", "FIELD_NOT_IN_SOURCE"}
        if state.get("repair_count", 0) < 1 and hasattr(self.extractor, "repair") and any(issue["code"] in repairable for issue in state.get("issues", [])):
            return "repair"
        return END

    def _repair(self, state: WorkflowState) -> dict:
        self._event(state, "repair", "fields_rechecked", "started", self.model_info.get("extraction", {}))
        from src.modules.extraction.domain.financial import ExtractionPayload
        previous = ExtractionPayload.model_validate(state["payload"])
        revised = self.extractor.repair(self._load_cdr(state), state["document_type"], previous, state.get("issues", []))
        self._event(state, "repair", "fields_rechecked", details={"attempt": state.get("repair_count", 0) + 1, **self.model_info.get("extraction", {})})
        return {"payload": revised.model_dump(mode="json"), "repair_count": state.get("repair_count", 0) + 1}

    def run(self, job_id: str, file_id: str, file_path: str, content_type: str, extension: str) -> WorkflowState:
        return self.graph.invoke({"job_id": job_id, "file_id": file_id, "file_path": file_path, "content_type": content_type, "extension": extension})
