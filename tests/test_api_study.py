import uuid


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
