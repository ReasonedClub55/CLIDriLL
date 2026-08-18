from pathlib import Path

from app.content_validation import validate_deck_dir

DECKS_DIR = Path(__file__).resolve().parent.parent / "content" / "decks"


def test_shipped_decks_are_valid():
    decks = validate_deck_dir(DECKS_DIR)
    slugs = {deck.slug for deck in decks}
    assert {"curl", "nmap", "http-syntax"} <= slugs
    for deck in decks:
        assert len(deck.questions) > 0
