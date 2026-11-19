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
    def __init__(self, readers: dict, extractor, artifact_dir: Path):
        self.readers = readers
        self.extractor = extractor
        self.artifact_dir = artifact_dir
        self.graph = self._build_graph()

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
        reader = self.readers.get(state["extension"].lower())
        if reader is None:
            return {"reader_status": "FAILED", "status": "failed", "error_code": "UNSUPPORTED_FILE_TYPE"}
        cdr = reader.read(state["file_id"], Path(state["file_path"]), state["content_type"])
        target = self.artifact_dir / state["job_id"]
        target.mkdir(parents=True, exist_ok=True)
        artifact = target / "cdr-v1.json"
        temporary = target / "cdr-v1.tmp"
        temporary.write_text(cdr.model_dump_json(indent=2))
        os.replace(temporary, artifact)
        if cdr.reader_status == ReaderStatus.FAILED:
            code = cdr.warnings[0].code if cdr.warnings else "NO_READABLE_CONTENT"
            return {"cdr_ref": str(artifact), "reader_status": "FAILED", "status": "failed", "error_code": code}
        return {"cdr_ref": str(artifact), "reader_status": cdr.reader_status.value}

    def _load_cdr(self, state: WorkflowState) -> CDR:
        return CDR.model_validate_json(Path(state["cdr_ref"]).read_text())

    def _classify(self, state: WorkflowState) -> dict:
        kind = classify(self._load_cdr(state))
        if kind == "unsupported":
            return {"document_type": kind, "status": "unsupported"}
        if kind == "unknown":
            return {"document_type": kind, "status": "needs_review", "error_code": "UNKNOWN_DOCUMENT_TYPE"}
        return {"document_type": kind}

    def _extract(self, state: WorkflowState) -> dict:
        if self.extractor is None:
            return {"status": "failed", "error_code": "MODEL_NOT_CONFIGURED"}
        payload = self.extractor.extract(self._load_cdr(state), state["document_type"])
        return {"payload": payload.model_dump(mode="json")}

    def _validate(self, state: WorkflowState) -> dict:
        if "payload" not in state:
            return {"status": "failed", "error_code": state.get("error_code", "EXTRACTION_FAILED")}
        from src.modules.extraction.domain.financial import ExtractionPayload
        payload = ExtractionPayload.model_validate(state["payload"])
        payload, normalization_issues = normalize(payload)
        issues = normalization_issues + validate(payload, self._load_cdr(state))
        status = "needs_review" if state["reader_status"] == "PARTIAL" or any(issue.severity == "high" for issue in issues) else "completed"
        return {"payload": payload.model_dump(mode="json"), "issues": [issue.model_dump() for issue in issues], "status": status}

    def _after_validation(self, state: WorkflowState):
        repairable = {"TOTAL_MISMATCH", "TOTAL_NOT_IN_SOURCE", "INVALID_EVIDENCE"}
        if state.get("repair_count", 0) < 1 and hasattr(self.extractor, "repair") and any(issue["code"] in repairable for issue in state.get("issues", [])):
            return "repair"
        return END

    def _repair(self, state: WorkflowState) -> dict:
        from src.modules.extraction.domain.financial import ExtractionPayload
        previous = ExtractionPayload.model_validate(state["payload"])
        revised = self.extractor.repair(self._load_cdr(state), state["document_type"], previous, state.get("issues", []))
        return {"payload": revised.model_dump(mode="json"), "repair_count": state.get("repair_count", 0) + 1}

    def run(self, job_id: str, file_id: str, file_path: str, content_type: str, extension: str) -> WorkflowState:
        return self.graph.invoke({"job_id": job_id, "file_id": file_id, "file_path": file_path, "content_type": content_type, "extension": extension})
