from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi import HTTPException
from sqlalchemy import text as sql_text

from src.core.config import settings
from src.infrastructure.database.session import init_db, engine
from src.modules.file_upload.adapters.inbound.rest.router import router as file_upload_router
from src.modules.extraction.adapters.inbound.rest.router import router as extraction_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown routines."""
    logger.info("Initializing database schema...")
    try:
        init_db()
        logger.info("Database tables initialized successfully.")
    except Exception as exc:
        logger.warning(
            f"Could not initialize database on startup (DB might still be starting): {exc}"
        )
    yield
    logger.info("Shutting down application...")


# OpenAPI Swagger Tag Metadata
tags_metadata = [
    {
        "name": "files",
        "description": (
            "**Invoice File Upload & Storage Management**.\n\n"
            "Handles multipart upload, pre-registration of metadata with `PENDING` status, "
            "physical write to persistent volume storage with `uuid.extension`, status finalization (`SUCCESS` / `FAILED`), "
            "paginated listing, and physical file download."
        ),
    },
    {
        "name": "general",
        "description": "General system health and service availability endpoints.",
    },
]

# Rich Markdown Description for Swagger UI
api_description = """
# 📑 Invoice Extract & Bill Processing API

Welcome to the **Invoice Extract API** built with **Hexagonal Clean Architecture** (Ports and Adapters), **Domain-Driven Design (DDD)**, and **SOLID Principles**.

---

## 🏗️ Architecture & Design
- **Domain Layer (`domain/`)**: Pure domain models (`UploadedFile`, `UploadStatus`), invariants, and lifecycle transitions.
- **Application Layer (`application/`)**: Use cases, CQRS commands & queries, ports (`inbound/`, `outbound/`), and application DTOs.
- **Adapters Layer (`adapters/`)**:
  - **Inbound REST**: FastAPI controllers, Pydantic schemas, and web response mappers.
  - **Outbound Persistence**: PostgreSQL database via SQLAlchemy repository.
  - **Outbound Storage**: Persistent volume storage (Docker volume `/app/uploads`).

---

## 🚀 Key Features in File Upload
1. **No Overwrites**: Original file name is preserved in database metadata while storage uses unique `UUID.ext`.
2. **Pre-determined Path in `PENDING` State**: Database registers the path and `PENDING` status *before* file writing begins.
3. **Physical Volume Persistence**: Files are written into `/app/uploads` (mounted Docker volume).
4. **Status Finalization**: Record transitions to `SUCCESS` upon successful disk write or `FAILED` on error.
"""

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=api_description,
    summary="Invoice bill extraction and storage system with PostgreSQL and persistent volume storage.",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2,
        "tryItOutEnabled": True,
    },
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Module Routers
app.include_router(file_upload_router)
app.include_router(extraction_router)


@app.get("/", include_in_schema=False)
def redirect_to_swagger():
    """Redirect root path to interactive Swagger documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["general"], summary="Health check")
def health_check():
    """Health check endpoint to verify API server is alive."""
    return {"status": "healthy", "app": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/health/live", tags=["general"])
def health_live():
    return {"status": "live"}


@app.get("/health/ready", tags=["general"])
def health_ready():
    try:
        with engine.connect() as connection:
            connection.execute(sql_text("SELECT 1"))
    except Exception:
        raise HTTPException(status_code=503, detail="DATABASE_UNAVAILABLE")
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
