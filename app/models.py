"""SQLAlchemy ORM models: Deck, Question, Progress, StudySession.

Mirrors the data model in plan.md §5. Single implicit local user, so no
user_id column anywhere yet -- every table is shaped so adding one later
(for multi-user) is an additive migration, not a rewrite.
"""
import enum
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DeckSource(str, enum.Enum):
    PORTED = "ported"
    AUTHORED = "authored"


class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FREE_RESPONSE = "free_response"
    SHORT_ANSWER = "short_answer"


class QuestionSource(str, enum.Enum):
    MAN = "man"
    HELP = "--help"
    HAND = "hand"


class ProgressBucket(str, enum.Enum):
    NEW = "new"
    LEARNING = "learning"
    KNOWN = "known"


class Deck(Base):
    __tablename__ = "decks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    source: Mapped[DeckSource] = mapped_column(Enum(DeckSource))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )
    sessions: Mapped[list["StudySession"]] = relationship(
        back_populates="deck", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), index=True)
    type: Mapped[QuestionType] = mapped_column(Enum(QuestionType))
    prompt: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    choices: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    example: Mapped[str | None] = mapped_column(Text, default=None)
    tags: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    source: Mapped[QuestionSource | None] = mapped_column(Enum(QuestionSource), default=None)
    raw_excerpt: Mapped[str | None] = mapped_column(Text, default=None)

    deck: Mapped["Deck"] = relationship(back_populates="questions")
    progress: Mapped["Progress | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )


class Progress(Base):
    __tablename__ = "progress"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"), unique=True, index=True
    )
    bucket: Mapped[ProgressBucket] = mapped_column(
        Enum(ProgressBucket), default=ProgressBucket.NEW
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    times_correct: Mapped[int] = mapped_column(Integer, default=0)
    times_wrong: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped["Question"] = relationship(back_populates="progress")


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    wrong_count: Mapped[int] = mapped_column(Integer, default=0)

    deck: Mapped["Deck"] = relationship(back_populates="sessions")
