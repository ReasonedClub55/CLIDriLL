"""SQLAlchemy engine/session setup.

Exposes the declarative Base that app/models.py builds on, plus the
engine/session plumbing used by the running app (app/main.py), the startup
seeder (app/seed.py), and tests. DB location comes from app/config.py.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
