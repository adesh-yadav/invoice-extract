"""responses — HTTP REST response schemas with OpenAPI / Swagger documentation metadata."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class FileUploadResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "original_name": "vendor_invoice_march_2024.pdf",
                "stored_name": "550e8400-e29b-41d4-a716-446655440000.pdf",
                "file_extension": ".pdf",
                "content_type": "application/pdf",
                "file_size_bytes": 1048576,
                "status": "SUCCESS",
                "error_message": None,
                "created_at": "2026-11-19T13:40:00Z",
                "updated_at": "2026-11-19T13:40:01Z",
            }
        },
    )

    id: str = Field(
        ...,
        description="Unique identifier (UUID) assigned to the uploaded file.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    original_name: str = Field(
        ...,
        description="Original name of the file uploaded by the user.",
        examples=["vendor_invoice_march_2024.pdf"],
    )
    stored_name: str = Field(
        ...,
        description="Sanitized unique file name on storage (uuid.extension) preventing file collisions.",
        examples=["550e8400-e29b-41d4-a716-446655440000.pdf"],
    )
    file_extension: str = Field(
        ...,
        description="File format extension (including dot).",
        examples=[".pdf", ".jpg", ".png"],
    )
    content_type: str = Field(
        ...,
        description="MIME type of the uploaded file.",
        examples=["application/pdf", "image/png", "image/jpeg"],
    )
    file_size_bytes: int = Field(
        ...,
        description="Total size of the persisted file in bytes.",
        examples=[1048576],
    )
    status: str = Field(
        ...,
        description="Lifecycle status: PENDING (pre-registered in DB), SUCCESS (written to volume), or FAILED.",
        examples=["SUCCESS", "PENDING", "FAILED"],
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Detailed error message if the upload or physical save failed.",
        examples=[None],
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when the file record was initially created in PENDING state.",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of the latest status transition or update.",
    )


class FileListResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total": 1,
                "files": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "original_name": "vendor_invoice_march_2024.pdf",
                        "stored_name": "550e8400-e29b-41d4-a716-446655440000.pdf",
                        "file_extension": ".pdf",
                        "content_type": "application/pdf",
                        "file_size_bytes": 1048576,
                        "status": "SUCCESS",
                        "error_message": None,
                        "created_at": "2026-11-19T13:40:00Z",
                        "updated_at": "2026-11-19T13:40:01Z",
                    }
                ],
            }
        }
    )

    total: int = Field(..., description="Total count of files returned in this query.")
    files: list[FileUploadResponse] = Field(
        ...,
        description="List of uploaded file metadata records.",
    )


class ErrorDetail(BaseModel):
    """Standardized error response model for OpenAPI / Swagger."""
    detail: str = Field(
        ...,
        description="Detailed description of the error encountered.",
        examples=["File with id '550e8400-e29b-41d4-a716-446655440000' not found."],
    )
