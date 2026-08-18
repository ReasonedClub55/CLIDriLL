# v2 — Dockerized, man-page-sourced edition

Content is parsed from real man pages (or `--help` fallback) at Docker image
build time and served statically at runtime — no network access needed once built.

Planned layout (not yet implemented — see [`../docs/prd-v2-docker.md`](../docs/prd-v2-docker.md)):
- `Dockerfile` — installs man-db + the tool list, runs the generator at build time
- `docker-compose.yml` — single service, binds `127.0.0.1:<port>` → `8080`
- `build/generate_items.py` — parses man pages / `--help` into `app/generated-items.json`
- `app/` — `index.html`, `app.js`, `curated-scenarios.js`, `generated-items.json` (generated)
- `server/` — minimal static file server (e.g. Python `http.server` or a tiny Express app)

Run once implemented:
```bash
docker compose up --build   # build & run
docker compose down         # stop
```
