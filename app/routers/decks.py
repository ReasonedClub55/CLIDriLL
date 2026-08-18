"""Deck and question CRUD endpoints.

Question create/update payloads are validated through
content_validation.QuestionIn -- the same per-type rules (multiple_choice
needs >=2 choices, short_answer/free_response must not have choices) that
gate content/decks/*.json at seed time, so hand-authored and API-authored
questions can never diverge.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.content_validation import QuestionIn
from app.database import get_db
from app.models import Deck, Question
from app.schemas import (
    DeckCreate,
    DeckOut,
    DeckUpdate,
    DeckWithQuestionsOut,
    QuestionOut,
    QuestionUpdate,
)

router = APIRouter(prefix="/api/decks", tags=["decks"])


def _get_deck_or_404(db: Session, deck_id: int) -> Deck:
    deck = db.get(Deck, deck_id)
    if deck is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"deck {deck_id} not found")
    return deck


def _get_question_or_404(db: Session, deck_id: int, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None or question.deck_id != deck_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"question {question_id} not found in deck {deck_id}",
        )
    return question


def _slug_taken(db: Session, slug: str, exclude_deck_id: int | None = None) -> bool:
    stmt = select(Deck).where(Deck.slug == slug)
    if exclude_deck_id is not None:
        stmt = stmt.where(Deck.id != exclude_deck_id)
    return db.scalar(stmt) is not None


@router.get("", response_model=list[DeckOut])
def list_decks(db: Session = Depends(get_db)):
    return db.scalars(select(Deck).order_by(Deck.title)).all()


@router.post("", response_model=DeckOut, status_code=status.HTTP_201_CREATED)
def create_deck(payload: DeckCreate, db: Session = Depends(get_db)):
    if _slug_taken(db, payload.slug):
        raise HTTPException(status.HTTP_409_CONFLICT, f"slug '{payload.slug}' already exists")
    deck = Deck(**payload.model_dump())
    db.add(deck)
    db.commit()
    db.refresh(deck)
    return deck


@router.get("/{deck_id}", response_model=DeckWithQuestionsOut)
def get_deck(deck_id: int, db: Session = Depends(get_db)):
    return _get_deck_or_404(db, deck_id)


@router.patch("/{deck_id}", response_model=DeckOut)
def update_deck(deck_id: int, payload: DeckUpdate, db: Session = Depends(get_db)):
    deck = _get_deck_or_404(db, deck_id)
    updates = payload.model_dump(exclude_unset=True)
    if "slug" in updates and updates["slug"] != deck.slug and _slug_taken(db, updates["slug"], deck_id):
        raise HTTPException(status.HTTP_409_CONFLICT, f"slug '{updates['slug']}' already exists")
    for field, value in updates.items():
        setattr(deck, field, value)
    db.commit()
    db.refresh(deck)
    return deck


@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deck(deck_id: int, db: Session = Depends(get_db)):
    deck = _get_deck_or_404(db, deck_id)
    db.delete(deck)
    db.commit()


@router.post(
    "/{deck_id}/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED
)
def create_question(deck_id: int, payload: QuestionIn, db: Session = Depends(get_db)):
    _get_deck_or_404(db, deck_id)
    question = Question(deck_id=deck_id, **payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.get("/{deck_id}/questions/{question_id}", response_model=QuestionOut)
def get_question(deck_id: int, question_id: int, db: Session = Depends(get_db)):
    return _get_question_or_404(db, deck_id, question_id)


@router.patch("/{deck_id}/questions/{question_id}", response_model=QuestionOut)
def update_question(
    deck_id: int, question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)
):
    question = _get_question_or_404(db, deck_id, question_id)
    updates = payload.model_dump(exclude_unset=True)

    merged = {
        field: updates.get(field, getattr(question, field))
        for field in (
            "type", "prompt", "answer", "choices", "example", "tags", "source", "raw_excerpt",
        )
    }
    try:
        validated = QuestionIn.model_validate(merged)
    except Exception as exc:  # pydantic.ValidationError
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(exc)) from exc

    for field, value in validated.model_dump().items():
        setattr(question, field, value)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/{deck_id}/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_question(deck_id: int, question_id: int, db: Session = Depends(get_db)):
    question = _get_question_or_404(db, deck_id, question_id)
    db.delete(question)
    db.commit()
