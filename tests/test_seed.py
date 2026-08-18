import json

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app import seed as seed_module
from app.content_validation import ContentValidationError
from app.database import Base
from app.models import Deck
from app.seed import seed_if_empty


def _fresh_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def test_seed_loads_valid_deck_files(tmp_path, monkeypatch):
    (tmp_path / "sample.json").write_text(
        json.dumps(
            {
                "slug": "sample",
                "title": "Sample",
                "source": "authored",
                "questions": [{"type": "short_answer", "prompt": "2+2?", "answer": "4"}],
            }
        )
    )
    monkeypatch.setattr(seed_module.settings, "content_decks_dir", tmp_path)

    db = _fresh_session()
    seed_if_empty(db)

    decks = db.scalars(select(Deck)).all()
    assert len(decks) == 1
    assert decks[0].slug == "sample"
    assert len(decks[0].questions) == 1


def test_seed_is_noop_when_decks_exist(tmp_path, monkeypatch):
    (tmp_path / "broken.json").write_text("{not valid json")
    monkeypatch.setattr(seed_module.settings, "content_decks_dir", tmp_path)

    db = _fresh_session()
    db.add(Deck(slug="existing", title="Existing", source="authored"))
    db.commit()

    seed_if_empty(db)  # must not touch broken.json since the DB isn't empty

    decks = db.scalars(select(Deck)).all()
    assert len(decks) == 1
    assert decks[0].slug == "existing"


def test_seed_raises_on_invalid_deck_file(tmp_path, monkeypatch):
    (tmp_path / "broken.json").write_text("{not valid json")
    monkeypatch.setattr(seed_module.settings, "content_decks_dir", tmp_path)

    db = _fresh_session()
    with pytest.raises(ContentValidationError):
        seed_if_empty(db)
