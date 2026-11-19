"""router — HTTP REST inbound adapter exposing file upload and retrieval endpoints."""
from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, Path as FastPath, Query, UploadFile, status
from fastapi.responses import FileResponse

from src.modules.file_upload.adapters.inbound.rest import mappers
from src.modules.file_upload.adapters.inbound.rest.schemas.responses import (
    ErrorDetail,
    FileListResponse,
    FileUploadResponse,
)
from src.modules.file_upload.application.dto.commands import UploadFileInput
from src.modules.file_upload.application.dto.queries import GetFileInput, ListFilesInput
from src.modules.file_upload.application.ports.inbound.get_file import GetFileQuery
from src.modules.file_upload.application.ports.inbound.list_files import ListFilesQuery
from src.modules.file_upload.application.ports.inbound.upload_file import UploadFileUseCase
from src.modules.file_upload.config.module import (
    get_get_file_query,
    get_list_files_query,
    get_upload_file_use_case,
)
from src.modules.file_upload.adapters.inbound.rest.validation import validate_upload, UploadValidationError

router = APIRouter(prefix="/v1/files", tags=["files"])


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload invoice bill file",
    operation_id="upload_file",
    responses={
        201: {
            "model": FileUploadResponse,
            "description": "File successfully recorded in DB and persisted to storage volume.",
        },
        400: {
            "model": ErrorDetail,
            "description": "Bad Request: File name is empty or file input is invalid.",
        },
        500: {
            "model": ErrorDetail,
            "description": "Internal Server Error: Database failure or disk write error.",
        },
    },
    description="""
Upload an invoice bill (PDF, image, etc.).

**Lifecycle Workflow:**
1. **Pre-determination**: Unique UUID-based file path (`/app/uploads/{uuid}.ext`) is generated upfront.
2. **Database Pre-registration**: Metadata row is created in the PostgreSQL `uploaded_files` table with `status = PENDING` and `file_path` already populated.
3. **Physical Write**: The file stream is physically written into the mounted persistent volume.
4. **Finalization**: Status is marked as `SUCCESS` and final byte size is recorded. If any error occurs, status transitions to `FAILED`.
""",
)
async def upload_file(
    file: UploadFile = File(
        ...,
        description="The invoice bill document to upload (PDF, PNG, JPG, JPEG, TIFF).",
    ),
    use_case: UploadFileUseCase = Depends(get_upload_file_use_case),
) -> FileUploadResponse:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot be empty.",
        )

    try:
        verified_content_type = validate_upload(file.file, file.filename)
    except UploadValidationError as exc:
        await file.close()
        raise HTTPException(status_code=exc.http_status, detail=exc.code)

    request = UploadFileInput(
        filename=file.filename,
        content_type=verified_content_type,
        file_stream=file.file,
    )

    try:
        view = use_case.handle(request)
        return mappers.to_file_response(view)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upload processing failed",
        )
    finally:
        await file.close()


@router.get(
    "/{file_id}",
    response_model=FileUploadResponse,
    summary="Get file details by ID",
    operation_id="get_file_by_id",
    responses={
        200: {
            "model": FileUploadResponse,
            "description": "File metadata details retrieved successfully.",
        },
        404: {
            "model": ErrorDetail,
            "description": "File not found with the specified ID.",
        },
    },
    description="Retrieve public metadata and lifecycle status for an uploaded file using its UUID.",
)
def get_file(
    file_id: str = FastPath(
        ...,
        description="The UUID identifier of the uploaded file.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    query: GetFileQuery = Depends(get_get_file_query),
) -> FileUploadResponse:
    view = query.handle(GetFileInput(file_id=file_id))
    if not view:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found.",
        )
    return mappers.to_file_response(view)


@router.get(
    "",
    response_model=FileListResponse,
    summary="List uploaded files",
    operation_id="list_files",
    responses={
        200: {
            "model": FileListResponse,
            "description": "Paginated list of uploaded file records.",
        },
    },
    description="Retrieve a paginated list of uploaded invoice files ordered by most recent first.",
)
def list_files(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of file records to return (1-100).",
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip for pagination.",
    ),
    query: ListFilesQuery = Depends(get_list_files_query),
) -> FileListResponse:
    views = query.handle(ListFilesInput(limit=limit, offset=offset))
    return mappers.to_file_list_response(views)


@router.get(
    "/{file_id}/download",
    summary="Download physical invoice file",
    operation_id="download_file",
    responses={
        200: {
            "description": "Binary file content stream with Content-Disposition headers using original filename.",
        },
        404: {
            "model": ErrorDetail,
            "description": "File not found in database or missing on physical storage volume.",
        },
    },
    description="Stream the physical binary file stored on the persistent volume back to the client using its original filename.",
)
def download_file(
    file_id: str = FastPath(
        ...,
        description="The UUID identifier of the file to download.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    ),
    query: GetFileQuery = Depends(get_get_file_query),
):
    view = query.handle(GetFileInput(file_id=file_id))
    if not view or not view.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with id '{file_id}' not found.",
        )

    file_path = Path(view.file_path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Physical file does not exist on storage volume.",
        )

    return FileResponse(
        path=file_path,
        filename=view.original_name,
        media_type=view.content_type,
    )
