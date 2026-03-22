"""Database session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from cultivos.config import get_settings
from cultivos.db.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.db_url else {}
        _engine = create_engine(settings.db_url, connect_args=connect_args)
        Base.metadata.create_all(bind=_engine)
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal


def get_db():
    """FastAPI dependency — yields a DB session per request."""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
