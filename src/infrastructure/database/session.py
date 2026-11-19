from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from src.core.config import settings

# Ensure psycopg2 driver is explicitly used if scheme is generic postgresql://
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db_session() -> Generator[Session, None, None]:
    """Dependency that provides an active database session and ensures it closes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create all registered database tables."""
    import src.modules.file_upload.adapters.outbound.persistence.models  # noqa: F401
    import src.modules.extraction.adapters.outbound.persistence.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
