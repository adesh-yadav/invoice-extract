"""Versioned, provider-neutral observations from document readers."""
from __future__ import annotations
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class ReaderStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Warning(BaseModel):
    code: str
    severity: str = "medium"
    message: str
    region_bbox: tuple[float, float, float, float] | None = None


class TextBlock(BaseModel):
    block_id: str
    text: str
    order: int
    kind: str = "line"
    bbox: tuple[float, float, float, float] | None = None
    source: str
    confidence: float | None = None
    confidence_provider: str | None = None


class Table(BaseModel):
    table_id: str
    rows: list[list[str]] = Field(default_factory=list)
    order: int


class Page(BaseModel):
    page_number: int = Field(ge=1)
    width: float | None = None
    height: float | None = None
    coordinate_system: str = "normalized_0_to_1"
    methods: list[str] = Field(default_factory=list)
    text_blocks: list[TextBlock] = Field(default_factory=list)
    tables: list[Table] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)


class CDR(BaseModel):
    cdr_version: str = "1.0"
    file_id: str
    source_format: str
    reader_status: ReaderStatus
    pages: list[Page] = Field(default_factory=list)
    warnings: list[Warning] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_blocks(self):
        ids = [block.block_id for page in self.pages for block in page.text_blocks]
        if len(ids) != len(set(ids)):
            raise ValueError("CDR block IDs must be unique")
        return self

    def ordered_text(self) -> str:
        return "\n".join(block.text for page in self.pages for block in sorted(page.text_blocks, key=lambda b: b.order))

    def primary_text_pages(self) -> list[tuple[int, str]]:
        """Readable text per page, excluding alternative AI correction candidates."""
        return [
            (
                page.page_number,
                "\n".join(
                    block.text.strip()
                    for block in sorted(page.text_blocks, key=lambda block: block.order)
                    if block.text.strip() and not block.source.endswith("_candidate")
                ),
            )
            for page in self.pages
        ]
