"""Pydantic request/response schemas for the API layer.

These mirror the ORM shapes in app/models.py for read/write over HTTP.
Per-type content validation rules (e.g. multiple_choice needs >=2 choices)
live in app/content_validation.py: app/routers/decks.py uses
content_validation.QuestionIn directly as the question create/update body,
so hand-authored deck files and API-authored content share one set of
rules. Deck slugs reuse content_validation.SLUG_RE for the same reason.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.content_validation import SLUG_RE
from app.models import DeckSource, ProgressBucket, QuestionSource, QuestionType


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deck_id: int
    type: QuestionType
    prompt: str
    answer: str
    choices: list[str] | None = None
    example: str | None = None
    tags: list[str] | None = None
    source: QuestionSource | None = None
    raw_excerpt: str | None = None


class DeckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    title: str
    description: str | None = None
    source: DeckSource
    created_at: datetime
    updated_at: datetime


class DeckWithQuestionsOut(DeckOut):
    questions: list[QuestionOut] = []


def _validate_slug(v: str) -> str:
    if not SLUG_RE.match(v):
        raise ValueError(
            "'slug' must be lowercase alphanumeric words separated by single hyphens"
        )
    return v


class DeckCreate(BaseModel):
    slug: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str | None = None
    source: DeckSource = DeckSource.AUTHORED

    _check_slug = field_validator("slug")(_validate_slug)


class DeckUpdate(BaseModel):
    slug: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    source: DeckSource | None = None

    @field_validator("slug")
    @classmethod
    def _check_slug(cls, v: str | None) -> str | None:
        return _validate_slug(v) if v is not None else v


class QuestionUpdate(BaseModel):
    """Partial update payload for a question. Fields left unset are kept as
    on the existing row; the router merges this onto the current question
    and re-validates the result through content_validation.QuestionIn so
    per-type rules can't be violated by a partial edit."""

    type: QuestionType | None = None
    prompt: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)
    choices: list[str] | None = None
    example: str | None = None
    tags: list[str] | None = None
    source: QuestionSource | None = None
    raw_excerpt: str | None = None


class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    bucket: ProgressBucket
    last_seen_at: datetime | None = None
    times_correct: int
    times_wrong: int


class StudySessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    deck_id: int
    started_at: datetime
    finished_at: datetime | None = None
    correct_count: int
    wrong_count: int


class StudySessionCreate(BaseModel):
    deck_id: int


class AnswerSubmit(BaseModel):
    question_id: int
    correct: bool
