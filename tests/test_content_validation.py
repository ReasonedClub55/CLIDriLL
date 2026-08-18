import json

import pytest

from app.content_validation import ContentValidationError, validate_deck_file

VALID_DECK = {
    "slug": "curl",
    "title": "curl",
    "description": "curl flags and usage",
    "source": "ported",
    "questions": [
        {
            "type": "multiple_choice",
            "prompt": "Flag to follow HTTP redirects?",
            "answer": "-L",
            "choices": ["-L", "-o", "-v"],
            "example": "curl -L https://example.com",
            "tags": ["redirects"],
            "source": "hand",
        },
        {
            "type": "short_answer",
            "prompt": "Flag to send a POST request?",
            "answer": "-X POST",
        },
        {
            "type": "free_response",
            "prompt": "Construct a curl command that follows redirects and is silent.",
            "answer": "curl -L -s https://example.com",
        },
    ],
}


def write_deck(tmp_path, data, name="deck.json"):
    path = tmp_path / name
    path.write_text(json.dumps(data))
    return path


def test_valid_deck_passes(tmp_path):
    path = write_deck(tmp_path, VALID_DECK)
    deck = validate_deck_file(path)
    assert deck.slug == "curl"
    assert len(deck.questions) == 3


def test_invalid_json_fails(tmp_path):
    path = tmp_path / "deck.json"
    path.write_text("{not valid json")
    with pytest.raises(ContentValidationError, match="invalid JSON"):
        validate_deck_file(path)


def test_bad_slug_fails(tmp_path):
    data = json.loads(json.dumps(VALID_DECK))
    data["slug"] = "Not A Slug!"
    path = write_deck(tmp_path, data)
    with pytest.raises(ContentValidationError):
        validate_deck_file(path)


def test_multiple_choice_requires_choices(tmp_path):
    data = json.loads(json.dumps(VALID_DECK))
    data["questions"][0].pop("choices")
    path = write_deck(tmp_path, data)
    with pytest.raises(ContentValidationError, match="at least 2 choices"):
        validate_deck_file(path)


def test_multiple_choice_answer_must_be_in_choices(tmp_path):
    data = json.loads(json.dumps(VALID_DECK))
    data["questions"][0]["answer"] = "-Z"
    path = write_deck(tmp_path, data)
    with pytest.raises(ContentValidationError, match="must be one of"):
        validate_deck_file(path)


def test_short_answer_rejects_choices(tmp_path):
    data = json.loads(json.dumps(VALID_DECK))
    data["questions"][1]["choices"] = ["-X POST", "-X GET"]
    path = write_deck(tmp_path, data)
    with pytest.raises(ContentValidationError, match="must not have 'choices'"):
        validate_deck_file(path)


def test_missing_questions_fails(tmp_path):
    data = json.loads(json.dumps(VALID_DECK))
    data["questions"] = []
    path = write_deck(tmp_path, data)
    with pytest.raises(ContentValidationError):
        validate_deck_file(path)


def test_missing_file_fails(tmp_path):
    with pytest.raises(ContentValidationError, match="could not read file"):
        validate_deck_file(tmp_path / "does-not-exist.json")
