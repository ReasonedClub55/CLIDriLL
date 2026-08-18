# CLIDriLL — Command Line Interface Drilling Linux Library

CLIDriLL is a small, local study tool for drilling CLI flags, multi-flag command construction, and raw HTTP syntax until they stick.

> **Note:** This repo is mid-pivot to v3, a generic Quizlet-style study engine
> (FastAPI + SQLite) described in [`plan.md`](plan.md). The v1 (plain HTML)
> and v2 (Dockerized, man-page-sourced) editions described below were never
> fully implemented and have been archived under
> [`docs/archive/`](docs/archive/) for reference. This README will be rewritten
> for v3 in a later phase (see `plan.md` §9, Phase 4).

Why this exists: when you use security tooling daily you still forget exact flags, flag combinations, and HTTP request/response syntax. CLIDriLL quizzes you (self-graded) and weights missed items to repeat weak spots — no accounts, no external services, and no internet access required at runtime.

---

## Quick highlights
- Drill CLI flags and HTTP syntax with flashcards and self-graded quizzes.
- Two editions:
  - v1: Plain HTML + `data.js` — instant, no build, open `index.html` in a browser.
  - v2: Dockerized — man-page-sourced content generated at image build time.
- Spaced-repetition-like missed-item weighting (simple Leitner-style buckets).
- Local progress persistence via `localStorage` (or optional named Docker volume in v2).
- Single-user, local-first design bound to `127.0.0.1`.

---

## Editions / How it works

### v1 — Simple local HTML edition
- Tech: Plain HTML + vanilla JavaScript. No bundler, no server required.
- Files:
  - `index.html` — UI + quiz engine + styles
  - `data.js` — `DRILL_ITEMS` array (hand-authored seed items)
- Run:
  - Clone the repo and double-click `index.html` (open via `file://`) or open it in your browser.
  - The app loads `data.js` via a script tag (no fetch() calls, so it works without a server).
- Ideal when you want an ultralight, editable starting point and to add items by hand.

### v2 — Dockerized man-page-sourced edition
- Purpose: Generate quiz content from the real tools' man pages (or `--help` fallback) and serve a static quiz UI from a container.
- Key idea: parse man pages at image build time into `generated-items.json`, bake it into the image, and serve static files at runtime — no runtime network access or parsing.
- Components:
  - `Dockerfile` — installs man-db + selected tools and runs the generator at build time.
  - `docker-compose.yml` — single service bound to `127.0.0.1:<port>` → 8080 in container.
  - `build/generate_items.py` — parses man pages / `--help` into structured JSON.
  - `app/` — `index.html`, `app.js`, `curated-scenarios.js`, `generated-items.json` (output).
  - Minimal static server (Python http.server or tiny Express) to serve the pre-generated files.
- Run (example):
  - Ensure Docker Desktop is set to Linux containers (WSL2) — required on Windows 11.
  - Build & run:
    - docker compose up --build
  - Open: http://127.0.0.1:<port> (compose binds host port → 8080 inside container)
  - Stop:
    - docker compose down
- Notes:
  - The generator favors `man <tool>` output; if missing, it falls back to `<tool> --help` (including subcommand `--help` for multi-command tools).
  - Base image suggestion: `kalilinux/kali-rolling` (many security tools ship man pages there).
  - To refresh content after adding tools: edit the generator config/tool list and rebuild with `docker compose build --no-cache`.

---

## Data model (how drill items are represented)
Every item is an object with at least: `id`, `tool`, `category`, `prompt`, `answer`.
Optional fields: `example`, `tags`, `source`, `raw_excerpt`.

Example (hand-authored):
```js
{
  id: "curl-001",
  tool: "curl",
  category: "flag", // "flag" | "scenario" | "http-syntax"
  prompt: "Flag to follow HTTP redirects",
  answer: "-L, --location",
  example: "curl -L https://example.com",
  tags: ["redirects", "basics"]
}
```

Example (generated from man page; generator includes source info):
```json
{
  "id": "nmap-sS",
  "tool": "nmap",
  "category": "flag",
  "flag": "-sS",
  "prompt": "TCP SYN scan — description as parsed from the man page",
  "answer": "-sS",
  "source": "man",
  "raw_excerpt": "the original paragraph, for double-checking accuracy"
}
```

v1 seed data is a single `DRILL_ITEMS` array (edit `data.js`). v2 produces `app/generated-items.json` and merges it at load time with `curated-scenarios.js`.

---

## Features
P0 (must-have)
- Quiz mode: prompt shown, reveal answer, self-grade pass/fail (no brittle exact string matching).
- Flashcard/browse mode.
- Filter by tool and category.
- Leitner-style missed-item weighting (new / learning / known).
- Progress persisted via `localStorage`.
- Session summary with counts and items-to-revisit.

P1 (nice-to-have)
- Toggle quiz direction (flag → description vs description → flag).
- Source indicator for generated items (man vs `--help`).
- Optional named Docker volume for progress backup (only if needed).

Out of scope
- Runtime internet access
- Executing the real tools from the quiz (we only need their man pages)
- Multi-user or cloud sync

---

## Initial content scope
- Seed items for v1: ~20–25 core `curl` flags, ~20–25 `nmap` flags, plus HTTP syntax items and 5–10 scenarios.
- v2 initial tool list: `curl`, `nmap`, `hydra`, `docker` (CLI), `gobuster`, `netcat`, `tcpdump`, `smbclient`, `hashcat`.
- The design makes adding tools one-line changes to the generator config + rebuild.

---

## Development & contributor notes
- v1 goal: keep the app tiny and easy to edit. Add items by editing `data.js`.
- v2 goal: generator does heavy lifting at build time. Check `generated-items.json` after the first build and spot-check a few entries (man pages are semi-structured and parser heuristics may produce some imperfect entries).
- If a tool's man page is missing or poor, the generator falls back to `--help` output and records the `source` for trust signals.
- Windows note: Docker Desktop must be in Linux containers mode (WSL2). Bind the compose service to `127.0.0.1` to avoid exposing services on the LAN.

---

## Acceptance criteria (from PRD)
- [ ] `docker compose up --build` produces a working container with no network access needed after image build.
- [ ] Visiting `http://127.0.0.1:<port>` shows a quiz drawing from all configured tools plus curated scenarios.
- [ ] `generated-items.json` contains flag text traceable to actual man pages (or `--help`).
- [ ] Wrong answers reappear more often within and across sessions.
- [ ] Adding a new tool is one line in the generator's list + rebuild.
- [ ] Adding a curated scenario is one object in `curated-scenarios.js`.

---

## Example commands

v1 — open locally (no server):
- Double-click `index.html` or open it from your browser (file://)

v2 — Dockerized build & run:
```bash
# build and run (compose binds host port to container)
docker compose up --build

# stop
docker compose down
```

If you change the tool list or want a fresh parse:
```bash
docker compose build --no-cache
docker compose up
```

---

## How to add/extend content
- v1: edit `data.js` and add one object per drill item.
- v2: add the tool name to the generator's tool-list, rebuild the image, and verify `generated-items.json`; add curated scenarios in `app/curated-scenarios.js`.

---

## UX notes
- Single-page, keyboard-friendly: space/enter to reveal, 1/2 or keys to grade pass/fail.
- Big central quiz card; filters and mode toggles on top.
- Fast to open and start drilling — no setup screens.

---

## Project docs
- [`docs/archive/prd-v1-html.md`](docs/archive/prd-v1-html.md) — PRD for the v1 plain-HTML edition (archived).
- [`docs/archive/prd-v2-docker.md`](docs/archive/prd-v2-docker.md) — PRD for the v2 Dockerized, man-page-sourced edition (archived).
- [`plan.md`](plan.md) — v3 development plan (current).

## License
This repository includes a LICENSE file. See LICENSE for details.
