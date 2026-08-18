"""Pydantic request/response schemas for the API layer.

These mirror the ORM shapes in app/models.py for read/write over HTTP.
Per-type content validation rules (e.g. multiple_choice needs >=2 choices)
live in app/content_validation.py, not here -- routers.py (Phase 2) wires
that module in for create/update payloads so the API and the content-seed
path share one set of rules.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

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
