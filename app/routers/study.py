"""Study-session endpoints: start a session, pick the next question with
Leitner-style weighting, submit an answer, and finish a session.

Weighting favors buckets that need more practice (new > learning > known),
so wrong answers reappear more often -- per plan.md's acceptance criteria.
"""
import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Deck, Progress, ProgressBucket, Question, StudySession
from app.schemas import (
    AnswerSubmit,
    ProgressOut,
    QuestionOut,
    StudySessionCreate,
    StudySessionOut,
)
from app.utils import utcnow

router = APIRouter(prefix="/api/study", tags=["study"])

_BUCKET_WEIGHT = {
    ProgressBucket.NEW: 3,
    ProgressBucket.LEARNING: 2,
    ProgressBucket.KNOWN: 1,
}

_NEXT_BUCKET_ON_CORRECT = {
    ProgressBucket.NEW: ProgressBucket.LEARNING,
    ProgressBucket.LEARNING: ProgressBucket.KNOWN,
    ProgressBucket.KNOWN: ProgressBucket.KNOWN,
}


def _get_session_or_404(db: Session, session_id: int) -> StudySession:
    session = db.get(StudySession, session_id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"study session {session_id} not found")
    return session


@router.post("/sessions", response_model=StudySessionOut, status_code=status.HTTP_201_CREATED)
def start_session(payload: StudySessionCreate, db: Session = Depends(get_db)):
    if db.get(Deck, payload.deck_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"deck {payload.deck_id} not found")
    session = StudySession(deck_id=payload.deck_id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=StudySessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    return _get_session_or_404(db, session_id)


@router.get("/sessions/{session_id}/next", response_model=QuestionOut | None)
def next_question(session_id: int, db: Session = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    questions = db.scalars(select(Question).where(Question.deck_id == session.deck_id)).all()
    if not questions:
        return None

    weights = [
        _BUCKET_WEIGHT[q.progress.bucket if q.progress else ProgressBucket.NEW] for q in questions
    ]
    return random.choices(questions, weights=weights, k=1)[0]


@router.post("/sessions/{session_id}/answer", response_model=ProgressOut)
def submit_answer(session_id: int, payload: AnswerSubmit, db: Session = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    question = db.get(Question, payload.question_id)
    if question is None or question.deck_id != session.deck_id:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            f"question {payload.question_id} not found in this session's deck",
        )

    progress = question.progress
    if progress is None:
        # times_correct/times_wrong column defaults apply at INSERT flush,
        # not on construction -- set them explicitly since we increment
        # below before the row is ever flushed.
        progress = Progress(
            question_id=question.id,
            bucket=ProgressBucket.NEW,
            times_correct=0,
            times_wrong=0,
        )
        db.add(progress)

    progress.last_seen_at = utcnow()
    if payload.correct:
        progress.times_correct += 1
        progress.bucket = _NEXT_BUCKET_ON_CORRECT[progress.bucket]
        session.correct_count += 1
    else:
        progress.times_wrong += 1
        progress.bucket = ProgressBucket.LEARNING
        session.wrong_count += 1

    db.commit()
    db.refresh(progress)
    return progress


@router.post("/sessions/{session_id}/finish", response_model=StudySessionOut)
def finish_session(session_id: int, db: Session = Depends(get_db)):
    session = _get_session_or_404(db, session_id)
    session.finished_at = utcnow()
    db.commit()
    db.refresh(session)
    return session
