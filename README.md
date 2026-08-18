# CLIDriLL — a small, local Quizlet-style study app

CLIDriLL is a local-first study app: pick a deck, study it via quiz mode
(multiple choice, short answer, or self-graded free response) or flashcards,
and let missed items reappear more often until they stick. It runs as a
single Docker container on your own machine — no accounts, no cloud, no
internet access needed at runtime.

The app ships with one deck ported from CLIDriLL's original purpose (drilling
`curl`/`nmap` flags and raw HTTP syntax), but the engine itself is generic:
any subject can be a deck.

---

## Quick start

```bash
docker compose up --build
```

Open http://127.0.0.1:8080. That's it — the app seeds its three starter
decks (`curl`, `nmap`, `HTTP Syntax`) into a SQLite database on first boot.

Stop it with:

```bash
docker compose down
```

Progress and any decks you add or edit survive `docker compose down` and
rebuilds — they live in a named Docker volume (`clidrill-data`), not inside
the container. If port 8080 is taken on your machine, set `CLIDRILL_PORT`:

```bash
CLIDRILL_PORT=8090 docker compose up --build
```

The container binds to `127.0.0.1` only — it's not reachable from other
devices on your network.

## Running without Docker (development)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080
```

This uses the same `app/`, `content/`, and `frontend/` code as the container;
`DATABASE_URL` defaults to a local `./clidrill.db` file (see `app/config.py`
for all env vars: `DATABASE_URL`, `HOST`, `PORT`, `CONTENT_DECKS_DIR`,
`FRONTEND_DIR`).

---

## How it works

- **Deck list** (`#/decks`) — every deck loaded from `content/decks/*.json`
  (plus any created through the API), with Study and Flashcards actions.
- **Quiz mode** (`#/study/:id`) — pulls questions one at a time, weighted so
  items you've missed (`learning` bucket) or never seen (`new`) come up more
  than ones you've gotten right repeatedly (`known`) — a simple Leitner
  scheme. Each question type is graded differently:
  - `multiple_choice` — click a choice, auto-graded against the answer.
  - `short_answer` — type an answer, auto-graded after normalizing
    (trim, lowercase, collapse whitespace) — good for a single flag or
    command name.
  - `free_response` — reveal the answer yourself and self-grade
    Pass/Fail — used for scenario/command-construction items where exact
    string matching would be too brittle.

  Every grading result is reported to the server, which owns progress state;
  the frontend only decides correct/incorrect for display.
- **Flashcards** (`#/flashcards/:id`) — read-only click-to-flip browsing
  through a deck's questions, no grading or progress writes.
- **Session summary** — ending a quiz session (or running out of questions)
  shows correct/wrong counts and accuracy for that session.

## Adding a new deck

Drop a new validated JSON file into `content/decks/` and restart the
container (or rerun `app/seed.py`'s startup path) — no code changes needed.
Validate it first:

```bash
python scripts/validate_content.py
```

This runs the same validation (`app/content_validation.py`) that gates
content at seed time and every deck/question write through the API, so a
malformed file is caught before it ever reaches the app. See `plan.md` §5–7
for the deck/question JSON shape and per-type rules (e.g. `multiple_choice`
needs ≥2 `choices` including the answer; `short_answer`/`free_response` must
not have `choices`).

## API

The frontend only talks to the backend through this JSON API — it never
touches the database or duplicates validation logic itself.

| Endpoint | Purpose |
|---|---|
| `GET /api/decks` | List decks |
| `POST /api/decks` | Create a deck |
| `GET /api/decks/{id}` | Deck + its questions |
| `PATCH /api/decks/{id}` / `DELETE /api/decks/{id}` | Edit / delete a deck |
| `POST /api/decks/{id}/questions` | Add a question to a deck |
| `PATCH /api/decks/{deck_id}/questions/{id}` / `DELETE ...` | Edit / delete a question |
| `POST /api/study/sessions` | Start a study session for a deck |
| `GET /api/study/sessions/{id}/next` | Next Leitner-weighted question |
| `POST /api/study/sessions/{id}/answer` | Submit a grading result, update progress |
| `POST /api/study/sessions/{id}/finish` | End the session |
| `GET /api/study/sessions/{id}` | Session state (for the summary screen) |

## Architecture

```
app/                # FastAPI backend
├── main.py          # app factory: startup (create tables + seed), routers, static frontend mount
├── config.py         # env-based settings (DATABASE_URL, HOST, PORT, content/frontend paths)
├── database.py        # SQLAlchemy engine/session
├── models.py           # Deck, Question, Progress, StudySession
├── schemas.py            # Pydantic API request/response schemas
├── content_validation.py  # the one place that knows what a valid deck/question looks like
├── seed.py                 # loads content/decks/*.json on first boot
└── routers/
    ├── decks.py             # deck/question CRUD
    └── study.py               # study sessions: next question, submit answer, finish

content/decks/*.json  # deck content (hand-authored or API-authored)
frontend/              # static HTML/CSS/JS, no build step, served by FastAPI
scripts/validate_content.py  # CLI: validate content/decks/*.json without starting the app
tests/                  # pytest suite (content validation, API, seeding)
```

Single implicit local user — no accounts or auth. Every table is shaped so
adding a `user_id` column later (for multi-user) would be additive, not a
rewrite; swapping SQLite for Postgres is a `DATABASE_URL` change, not a code
change. See `plan.md` for the full design rationale and the milestone plan
this app was built against.

## Development

```bash
pytest tests/                    # backend test suite
python scripts/validate_content.py  # validate deck content files
```

## Project docs
- [`plan.md`](plan.md) — the v3 development plan (architecture, data model,
  milestones, acceptance criteria) this app was built against.
- [`docs/archive/`](docs/archive/) — PRDs and stub folders for CLIDriLL's
  original two editions (v1: static HTML, v2: Docker + man-page-generated
  content), both superseded by this app and kept for history.

## License
This repository includes a LICENSE file. See LICENSE for details.
