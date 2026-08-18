"""Shared test fixtures.

Points the app at an isolated temp SQLite file (set before app.database is
ever imported, since the engine is built at module import time) so tests
never touch a developer's local clidrill.db.
"""
import os
import tempfile

_tmp_dir = tempfile.mkdtemp(prefix="clidrill-test-")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
