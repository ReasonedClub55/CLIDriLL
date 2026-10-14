import uuid

import pytest

from app.database import SessionLocal
from app.models import Progress
from app.schemas import ProgressOut


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _make_deck_with_question(client):
    deck = client.post("/api/decks", json={"slug": _slug("study"), "title": "T"}).json()
    question = client.post(
        f"/api/decks/{deck['id']}/questions",
        json={"type": "short_answer", "prompt": "p", "answer": "a"},
    ).json()
    return deck, question


def test_start_session_for_missing_deck_404s(client):
    resp = client.post("/api/study/sessions", json={"deck_id": 999999})
    assert resp.status_code == 404


def test_next_question_returns_null_for_empty_deck(client):
    deck = client.post("/api/decks", json={"slug": _slug("empty"), "title": "T"}).json()
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    resp = client.get(f"/api/study/sessions/{session['id']}/next")
    assert resp.status_code == 200
    assert resp.json() is None


def test_next_question_returns_deck_question(client):
    deck, question = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    resp = client.get(f"/api/study/sessions/{session['id']}/next")
    assert resp.status_code == 200
    assert resp.json()["id"] == question["id"]


def test_answer_bucket_progression(client):
    deck, question = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    sid = session["id"]

    r1 = client.post(
        f"/api/study/sessions/{sid}/answer",
        json={"question_id": question["id"], "correct": True},
    )
    assert r1.status_code == 200
    assert r1.json()["bucket"] == "learning"
    assert r1.json()["times_correct"] == 1

    r2 = client.post(
        f"/api/study/sessions/{sid}/answer",
        json={"question_id": question["id"], "correct": True},
    )
    assert r2.json()["bucket"] == "known"
    assert r2.json()["times_correct"] == 2

    r3 = client.post(
        f"/api/study/sessions/{sid}/answer",
        json={"question_id": question["id"], "correct": False},
    )
    assert r3.json()["bucket"] == "learning"
    assert r3.json()["times_wrong"] == 1

    session_state = client.get(f"/api/study/sessions/{sid}").json()
    assert session_state["correct_count"] == 2
    assert session_state["wrong_count"] == 1


def test_answer_for_question_outside_session_deck_404s(client):
    deck_a, _ = _make_deck_with_question(client)
    _, question_b = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck_a["id"]}).json()

    resp = client.post(
        f"/api/study/sessions/{session['id']}/answer",
        json={"question_id": question_b["id"], "correct": True},
    )
    assert resp.status_code == 404


def test_finish_session_sets_finished_at(client):
    deck, _ = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    assert session["finished_at"] is None

    finished = client.post(f"/api/study/sessions/{session['id']}/finish")
    assert finished.status_code == 200
    assert finished.json()["finished_at"] is not None


@pytest.mark.parametrize("correct", [True, False])
def test_finished_session_rejects_answers_without_changing_progress(client, correct):
    deck, question = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    sid = session["id"]
    answer = {"question_id": question["id"], "correct": True}
    before = client.post(f"/api/study/sessions/{sid}/answer", json=answer).json()
    finished = client.post(f"/api/study/sessions/{sid}/finish").json()

    response = client.post(
        f"/api/study/sessions/{sid}/answer",
        json={"question_id": question["id"], "correct": correct},
    )
    assert response.status_code == 409
    assert client.get(f"/api/study/sessions/{sid}").json() == finished

    # Verify the persistent question history, including last_seen_at, directly
    # in the same disposable test database used by the API.
    with SessionLocal() as db:
        progress = db.get(Progress, before["id"])
        assert ProgressOut.model_validate(progress).model_dump(mode="json") == before


def test_finished_session_does_not_offer_another_question(client):
    deck, _ = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    client.post(f"/api/study/sessions/{session['id']}/finish")
    assert client.get(f"/api/study/sessions/{session['id']}/next").status_code == 409


def test_finishing_again_preserves_original_finish_time(client):
    deck, _ = _make_deck_with_question(client)
    session = client.post("/api/study/sessions", json={"deck_id": deck["id"]}).json()
    url = f"/api/study/sessions/{session['id']}/finish"
    first = client.post(url)
    second = client.post(url)
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


@pytest.mark.parametrize("action", ["next", "answer", "finish"])
def test_missing_session_still_returns_404(client, action):
    url = f"/api/study/sessions/999999/{action}"
    if action == "next":
        response = client.get(url)
    elif action == "answer":
        response = client.post(url, json={"question_id": 999999, "correct": True})
    else:
        response = client.post(url)
    assert response.status_code == 404
