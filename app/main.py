"""FastAPI application factory.

Wires up DB startup (create tables + seed content), mounts the API routers,
and serves the static frontend if present. The frontend directory is
guarded so the backend still boots standalone before Phase 3 lands a real UI.
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import decks, study
from app.seed import seed_if_empty

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="CLIDriLL", version="3.0.0", lifespan=lifespan)

    app.include_router(decks.router)
    app.include_router(study.router)

    if settings.frontend_dir.is_dir():
        app.mount(
            "/", StaticFiles(directory=str(settings.frontend_dir), html=True), name="frontend"
        )

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
