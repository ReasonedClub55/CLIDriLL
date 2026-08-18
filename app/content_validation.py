"""Dedicated content validation module.

This is the ONE place that knows what a valid deck/question looks like.
Both the content-seeding path (app/seed.py, Phase 2) and the API
(app/routers/decks.py, Phase 2) import from here so hand-authored JSON
files and UI-authored content go through identical rules -- validation
logic must never be duplicated into frontend/js/*.js or inline in HTML.

scripts/validate_content.py is a thin CLI wrapper around
validate_deck_file() for checking content/decks/*.json before committing,
without starting the app.
"""
import json
import re
from pathlib import Path

from pydantic import BaseModel, Field, model_validator

from app.models import DeckSource, QuestionSource, QuestionType

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class ContentValidationError(Exception):
    """Raised when a deck file fails validation, with a path for context."""

    def __init__(self, path: str | Path, message: str):
        self.path = str(path)
        self.message = message
        super().__init__(f"{self.path}: {message}")


class QuestionIn(BaseModel):
    """Validated shape of one question, whether from a deck JSON file or an
    API create/update payload."""

    type: QuestionType
    prompt: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    choices: list[str] | None = None
    example: str | None = None
    tags: list[str] | None = None
    source: QuestionSource | None = None
    raw_excerpt: str | None = None

    @model_validator(mode="after")
    def _check_choices_match_type(self) -> "QuestionIn":
        if self.type == QuestionType.MULTIPLE_CHOICE:
            if not self.choices or len(self.choices) < 2:
                raise ValueError(
                    "multiple_choice questions must have at least 2 choices"
                )
            if self.answer not in self.choices:
                raise ValueError(
                    "multiple_choice 'answer' must be one of 'choices'"
                )
            if len(set(self.choices)) != len(self.choices):
                raise ValueError("multiple_choice 'choices' must not contain duplicates")
        else:
            if self.choices is not None:
                raise ValueError(
                    f"{self.type.value} questions must not have 'choices'"
                )
        return self


class DeckFile(BaseModel):
    """Validated shape of a deck JSON file (content/decks/<slug>.json)."""

    slug: str
    title: str = Field(min_length=1)
    description: str | None = None
    source: DeckSource
    questions: list[QuestionIn] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_slug(self) -> "DeckFile":
        if not SLUG_RE.match(self.slug):
            raise ValueError(
                "'slug' must be lowercase alphanumeric words separated by "
                "single hyphens (e.g. 'http-syntax')"
            )
        return self


def validate_deck_file(path: str | Path) -> DeckFile:
    """Load and validate a single deck JSON file.

    Raises ContentValidationError with the offending path and a readable
    message on any structural or content problem (bad JSON, missing
    fields, wrong types, per-question-type rule violations, etc).
    """
    path = Path(path)
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContentValidationError(path, f"could not read file: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContentValidationError(path, f"invalid JSON: {exc}") from exc

    try:
        return DeckFile.model_validate(data)
    except Exception as exc:  # pydantic.ValidationError
        raise ContentValidationError(path, str(exc)) from exc


def validate_deck_dir(directory: str | Path) -> list[DeckFile]:
    """Validate every *.json file in a directory. Raises on the first
    invalid file; returns the list of validated decks on full success."""
    directory = Path(directory)
    decks = []
    for deck_path in sorted(directory.glob("*.json")):
        decks.append(validate_deck_file(deck_path))
    return decks
