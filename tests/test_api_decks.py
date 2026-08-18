import uuid


def _slug(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def test_list_decks_includes_seeded_content(client):
    resp = client.get("/api/decks")
    assert resp.status_code == 200
    slugs = {d["slug"] for d in resp.json()}
    assert {"curl", "nmap", "http-syntax"} <= slugs


def test_deck_create_get_update_delete_lifecycle(client):
    slug = _slug("deck")
    create = client.post("/api/decks", json={"slug": slug, "title": "Title"})
    assert create.status_code == 201
    deck = create.json()
    assert deck["slug"] == slug
    assert deck["source"] == "authored"

    got = client.get(f"/api/decks/{deck['id']}")
    assert got.status_code == 200
    assert got.json()["questions"] == []

    patched = client.patch(f"/api/decks/{deck['id']}", json={"title": "New Title"})
    assert patched.status_code == 200
    assert patched.json()["title"] == "New Title"

    deleted = client.delete(f"/api/decks/{deck['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/decks/{deck['id']}").status_code == 404


def test_create_deck_duplicate_slug_conflicts(client):
    slug = _slug("dupe")
    assert client.post("/api/decks", json={"slug": slug, "title": "A"}).status_code == 201
    dupe = client.post("/api/decks", json={"slug": slug, "title": "B"})
    assert dupe.status_code == 409


def test_create_deck_bad_slug_rejected(client):
    resp = client.post("/api/decks", json={"slug": "Not A Slug!", "title": "A"})
    assert resp.status_code == 422


def test_get_missing_deck_404s(client):
    assert client.get("/api/decks/999999").status_code == 404


def test_question_create_get_update_delete_lifecycle(client):
    deck = client.post("/api/decks", json={"slug": _slug("deck"), "title": "T"}).json()

    created = client.post(
        f"/api/decks/{deck['id']}/questions",
        json={
            "type": "multiple_choice",
            "prompt": "p?",
            "answer": "a",
            "choices": ["a", "b"],
        },
    )
    assert created.status_code == 201
    question = created.json()

    got = client.get(f"/api/decks/{deck['id']}/questions/{question['id']}")
    assert got.status_code == 200

    patched = client.patch(
        f"/api/decks/{deck['id']}/questions/{question['id']}",
        json={"type": "short_answer", "choices": None, "answer": "a"},
    )
    assert patched.status_code == 200
    assert patched.json()["type"] == "short_answer"
    assert patched.json()["choices"] is None

    deleted = client.delete(f"/api/decks/{deck['id']}/questions/{question['id']}")
    assert deleted.status_code == 204
    assert client.get(f"/api/decks/{deck['id']}/questions/{question['id']}").status_code == 404


def test_create_question_invalid_type_rules_rejected(client):
    deck = client.post("/api/decks", json={"slug": _slug("deck"), "title": "T"}).json()
    resp = client.post(
        f"/api/decks/{deck['id']}/questions",
        json={"type": "free_response", "prompt": "p", "answer": "a", "choices": ["x", "y"]},
    )
    assert resp.status_code == 422


def test_update_question_rejects_rule_violation(client):
    deck = client.post("/api/decks", json={"slug": _slug("deck"), "title": "T"}).json()
    question = client.post(
        f"/api/decks/{deck['id']}/questions",
        json={"type": "short_answer", "prompt": "p", "answer": "a"},
    ).json()

    # switching to multiple_choice without supplying >=2 choices must fail
    resp = client.patch(
        f"/api/decks/{deck['id']}/questions/{question['id']}",
        json={"type": "multiple_choice"},
    )
    assert resp.status_code == 422
