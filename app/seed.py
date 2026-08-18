"""Loads content/decks/*.json into the database on first run.

Called from app/main.py's startup lifespan. If the decks table already has
rows, this is a no-op -- seeding only ever happens once against an empty
database, so it's safe to call on every boot. A malformed deck file raises
ContentValidationError, which is left to propagate so startup fails loudly
(per plan.md §7) instead of silently loading broken content.
"""
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.content_validation import validate_deck_dir
from app.models import Deck, Question

logger = logging.getLogger(__name__)


def seed_if_empty(db: Session) -> None:
    if db.query(Deck).first() is not None:
        return

    deck_files = validate_deck_dir(settings.content_decks_dir)
    for deck_file in deck_files:
        deck = Deck(
            slug=deck_file.slug,
            title=deck_file.title,
            description=deck_file.description,
            source=deck_file.source,
        )
        deck.questions = [
            Question(
                type=q.type,
                prompt=q.prompt,
                answer=q.answer,
                choices=q.choices,
                example=q.example,
                tags=q.tags,
                source=q.source,
                raw_excerpt=q.raw_excerpt,
            )
            for q in deck_file.questions
        ]
        db.add(deck)

    db.commit()
    logger.info("Seeded %d deck(s) from %s", len(deck_files), settings.content_decks_dir)
