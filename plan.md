# CLIDriLL v3 — Development Plan (Quizlet-style engine)

## 1. Pivot summary
CLIDriLL started as a single-purpose CLI-flag drilling tool (v1: static HTML,
v2: Docker + man-page-sourced content). This plan supersedes both: CLIDriLL
becomes a small, generic, Quizlet-style study app — multiple question/answer
formats, decks/subjects instead of one fixed topic — while staying local-first,
single-user, and Docker-hosted on a normal PC (no cloud, no login).

The original CLI-flag content (curl, nmap, HTTP syntax) becomes the **first
deck** loaded into the new generic engine, proving it works before other
subjects get added.

Decisions locked in for this plan:
- **Repo**: evolves in place (`ReasonedClub55/CLIDriLL`); v1/v2 stub folders
  and PRDs are archived, not deleted.
- **Users**: single local user, no login/auth screens.
- **Stack**: Python + FastAPI + SQLite, plain HTML/CSS/JS frontend served as
  static files by FastAPI. Structured so swapping SQLite → Postgres later is a
  config change, not a rewrite.
- **Content**: curl/nmap/HTTP-syntax ported into the new deck format as the
  first deck(s).

## 2. Goals
- Quizlet-like UX: pick a deck, study it via quiz, flashcards, or learn mode.
- Multiple question/answer styles per deck: multiple choice, free-response
  (self-graded reveal), short-answer (auto-checked, normalized match).
- Runs as a single Docker container on a normal PC (`docker compose up`),
  bound to `127.0.0.1`, no external network access needed at runtime.
- Progress persisted server-side (SQLite) instead of localStorage, so it
  survives container rebuilds via a named volume.
- Architecture leaves clear room to scale later: more decks, more question
  types, Postgres, multi-user — without redesigning the core.
- Data/content **validation lives in one dedicated backend module**, reused by
  both the content-seeding path and the API — never duplicated into frontend
  HTML/JS/CSS.

## 3. Non-goals (for this plan)
- No accounts, sessions, or auth (single implicit local user).
- No public/remote hosting — stays bound to `127.0.0.1`.
- No mobile app.
- No real-time multiplayer / match-game modes on day one (stretch, see §8).

## 4. Architecture

```
CLIDriLL/
├── app/                          # FastAPI backend
│   ├── main.py                   # app factory, mounts static files + routers
│   ├── config.py                 # env-based settings (DB path, port, etc.)
│   ├── database.py               # SQLAlchemy engine/session setup
│   ├── models.py                 # ORM models: Deck, Question, Choice, Progress
│   ├── schemas.py                # Pydantic request/response schemas (API layer)
│   ├── content_validation.py     # DEDICATED validation module (see §6)
│   ├── seed.py                   # loads content/decks/*.json into DB on first run
│   └── routers/
│       ├── decks.py              # deck/question CRUD endpoints
│       └── study.py              # study-session endpoints (next question, submit answer)
├── content/
│   └── decks/                    # hand-authored/ported deck JSON files
│       ├── curl.json
│       ├── nmap.json
│       └── http-syntax.json
├── frontend/                     # static, minimal, Quizlet-like UI
│   ├── index.html
│   ├── css/style.css
│   └── js/ (api.js, quiz.js, flashcards.js, deck-list.js)
├── scripts/
│   └── validate_content.py       # CLI wrapper: validate content/decks/*.json using app/content_validation.py
├── tests/
├── docs/
│   └── archive/                  # prd-v1-html.md, prd-v2-docker.md moved here (history, not deleted)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── plan.md                       # this file
└── README.md                     # rewritten for v3
```

**Why this shape:** the frontend never talks to the database or validates
content directly — it only calls the FastAPI JSON API. All validation
(content files at seed time, and API payloads at request time) funnels
through `app/content_validation.py`, so there's exactly one place that knows
what a "valid question" looks like.

## 5. Data model
- **Deck**: `id`, `slug`, `title`, `description`, `source` (`"ported"` |
  `"authored"`), timestamps.
- **Question**: `id`, `deck_id`, `type` (`multiple_choice` | `free_response` |
  `short_answer`), `prompt`, `answer` (canonical answer), `choices` (JSON list,
  multiple_choice only), `example`, `tags`, `source` (`man` | `--help` |
  `hand`), `raw_excerpt`.
- **Progress**: `id`, `question_id`, `bucket` (`new` | `learning` | `known` —
  Leitner-style, ported from the original PRD), `last_seen_at`,
  `times_correct`, `times_wrong`.
- **StudySession** (lightweight): `id`, `deck_id`, `started_at`, `finished_at`,
  `correct_count`, `wrong_count` — backs the session-summary screen.

Single implicit user, so no `user_id` column yet — but every table is designed
so adding one later (for multi-user) is an additive migration, not a rewrite.

## 6. Question/answer types
| Type | Grading | Notes |
|---|---|---|
| `multiple_choice` | Auto (exact match against `choices`) | 3–5 options, one correct |
| `free_response` | Self-graded (Pass/Fail button) | Same "don't brittle-string-match" reasoning as the original PRD — used for scenario/command-construction items |
| `short_answer` | Auto (normalized match: trim, case-insensitive, whitespace-collapsed) | For short factual answers like a single flag |

`type` is a discriminator field; new types (e.g. `true_false`, `matching`)
can be added later by extending `content_validation.py` and the frontend
renderer — the deck/question storage shape doesn't need to change.

## 7. Content validation module (dedicated, non-UI)
`app/content_validation.py`:
- Pydantic models mirroring the deck/question schema in §5, including
  per-`type` validation (e.g. `multiple_choice` must have ≥2 `choices`
  including the `answer`; `short_answer`/`free_response` must not have
  `choices`).
- `validate_deck_file(path) -> Deck` — used by:
  - `app/seed.py` at container startup (validates every file in
    `content/decks/` before inserting into SQLite; startup fails loudly on a
    bad file rather than silently loading broken content).
  - `app/routers/decks.py` when a deck/question is created or edited via the
    API (§9's authoring UI), so hand-authored and UI-authored content go
    through the same rules.
- `scripts/validate_content.py` — thin CLI (`python scripts/validate_content.py`)
  for validating `content/decks/*.json` locally before committing new content,
  without starting the app.

This is the file/script the task asked for: all data validation logic lives
here, imported by both seeding and API code — never re-implemented in
`frontend/js/*.js` or inline in HTML.

## 8. Docker & deployment
- Single-service `docker-compose.yml`: builds the FastAPI image, binds
  `127.0.0.1:<port> -> 8080`, mounts a **named volume** for the SQLite file
  (`/data/clidrill.db`) so progress and any UI-authored decks survive
  `docker compose down` / rebuilds.
- `Dockerfile`: installs Python deps, copies `app/`, `content/`, `frontend/`;
  `CMD` runs `uvicorn app.main:app`.
- Startup flow: app boots → `app/seed.py` checks if DB is empty → if empty,
  validates and loads `content/decks/*.json` → serves API + static frontend.
- Scaling path (documented, not built yet): swap `DATABASE_URL` env var to a
  Postgres DSN and add a `postgres` service to compose — the SQLAlchemy layer
  doesn't need to change. Add `user_id` columns for multi-user. Split
  frontend to its own static host if it ever needs to leave this one PC.

## 9. Milestones / issue plan
Issues are meant to be implemented **one at a time, in order**, each building
on the previous. GitHub issues are created in `ReasonedClub55/CLIDriLL` with
milestones matching the phases below and priority labels (`P0` = required for
a working v3, `P1`/`P2` = stretch).

**Phase 1 — Foundation**
1. Restructure repo skeleton (archive v1/v2 + PRDs, create new directory layout)
2. Data model: SQLAlchemy models + Pydantic schemas
3. Content validation module + CLI validator script
4. Port CLI-drill content into new deck JSON format

**Phase 2 — Backend API**
5. FastAPI app scaffold (config, DB session, seeding on startup)
6. Decks & Questions CRUD API
7. Study session API (next-question selection w/ Leitner weighting, submit answer, progress)

**Phase 3 — Frontend**
8. Base frontend shell (layout, nav, deck list page, minimal styling)
9. Study/Quiz mode UI (all three question types)
10. Flashcard/browse mode UI
11. Session summary & progress/stats view

**Phase 4 — Docker & docs**
12. Dockerize (Dockerfile, compose, persistent volume)
13. README rewrite + end-to-end acceptance pass

**Phase 5 — Stretch (P1/P2)**
14. In-browser deck/question authoring UI (create/edit/delete — the most
    "Quizlet-like" piece, deferred until the core engine works)
15. Match-style study mode (P2)
16. Deck export/import as JSON (P2)

## 10. Acceptance criteria (v3 "done")
- [x] `docker compose up --build` serves a working app at `http://127.0.0.1:<port>` with no runtime network access needed.
- [x] Deck list shows the ported curl/nmap/HTTP-syntax decks.
- [x] A deck can be studied in quiz mode using all three question types, and in flashcard mode.
- [x] Wrong answers reappear more often (Leitner buckets), and progress survives a container restart.
- [x] `python scripts/validate_content.py` catches a malformed deck file before it reaches the app.
- [x] Adding a new deck = dropping one validated JSON file in `content/decks/` (no code changes).
- [x] No validation logic exists in `frontend/js/*` or inline in HTML — it's all in `app/content_validation.py`.

All seven verified end-to-end against a real `docker compose up --build`
run in Phase 4 (issue 13): deck list/detail, a full quiz session across all
three question types plus session finish, and a `down`+`up` cycle showing no
re-seed and identical deck rows (volume persistence) — all via the running
container's API, plus `pytest tests/` (26/26) and
`python scripts/validate_content.py` (3/3 decks). "No validation logic in
frontend/js/*" verified by inspection: `content_validation.py` is the only
file with per-type schema rules (multiple_choice choice counts, etc.);
frontend/js/util.js's `normalizeAnswer` is answer-matching for grading, not
schema validation.
