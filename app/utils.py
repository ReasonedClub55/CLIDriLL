"""Small shared helpers with no natural home in models/schemas."""
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
