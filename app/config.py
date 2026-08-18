"""Environment-based application settings.

Centralizes env-var configuration (DB location, host/port, content/frontend
paths) so app/database.py, app/seed.py, and app/main.py all read from one
place instead of scattering os.environ.get() calls.
"""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings:
    database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./clidrill.db")
    host: str = os.environ.get("HOST", "127.0.0.1")
    port: int = int(os.environ.get("PORT", "8080"))
    content_decks_dir: Path = Path(
        os.environ.get("CONTENT_DECKS_DIR", str(REPO_ROOT / "content" / "decks"))
    )
    frontend_dir: Path = Path(
        os.environ.get("FRONTEND_DIR", str(REPO_ROOT / "frontend"))
    )


settings = Settings()
