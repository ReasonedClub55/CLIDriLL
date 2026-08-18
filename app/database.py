"""SQLAlchemy engine/session setup.

Full env-based configuration (DB path, port, etc.) lands in app/config.py in
Phase 2 alongside the FastAPI app scaffold. For now this module just exposes
the declarative Base that app/models.py builds on, plus enough engine/session
plumbing for models and content validation to be exercised (e.g. in tests)
without a running app.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./clidrill.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
