# PRD v2: CLI Flag & Syntax Drill Tool (Dockerized, Man-Page-Sourced)

> Supersedes the original single-HTML-file PRD. Same core goal — drill CLI flags
> and HTTP syntax until they stick — but now self-hosted via Docker, and content
> is sourced from real, installed man pages instead of hand-authored data, so
> accuracy comes from the actual tools rather than from memory (mine or yours).

## 1. Problem Statement
I keep forgetting exact flags/syntax for CLI tools I use in security work. A
hand-typed flag database risks quietly being wrong or stale. I want the tool's
content generated from the real man pages of the real tools, running self-hosted
on my own device via Docker, spun up quickly with no external hosting.

## 2. Goals
- Self-hosted via Docker/Docker Compose on a **Windows 11 host, run through Docker
  Desktop** — `docker compose up`, open a browser tab, study, `docker compose down`
  when finished. This is a spin-up/tear-down study tool, not a persistent service.
- Content accuracy comes from real, installed man pages baked into the image at
  build time — not from hand-typed or AI-recalled flag descriptions.
- Auto-generate quiz items (flag → description) directly from parsed man pages.
- Keep a small hand-curated layer for things man pages can't give you for free:
  multi-flag "build the full command from this scenario" drills, and HTTP raw
  syntax (request line, headers, status codes — not tied to any one tool's man page).
- Missed-item weighting (leitner-style buckets) so weak spots repeat more.
- No account system, no external network calls at runtime.

## 3. Non-Goals
- Not trying to run the actual tools (no live scanning, no real docker-in-docker).
  We only need their **man pages**, not their functionality.
- No public hosting — bind to `127.0.0.1` only; this never needs to leave your device.
- Not deployed to the Proxmox homelab, and not meant to run continuously — this
  lives on the Windows 11 machine via Docker Desktop, started when you want to
  study and stopped when you're done. No always-on assumptions anywhere in the design.
- Not attempting a fully general "any Linux tool" system on day one — fixed initial
  tool list (below), architected so adding a tool later means adding one entry to
  a config list and rebuilding the image.

## 4. Initial Tool Set
`curl`, `nmap`, `hydra`, `docker` (CLI), `gobuster`, `netcat`, `tcpdump`,
`smbclient`, `hashcat` — pulled from your actual lab work, not generic examples.

**Implementation note for Claude Code:** not every tool ships a traditional
`man(1)` page via apt on every base image — `docker` in particular is often
thinner on man pages than `--help` output. Content source per tool should be:
try `man <tool>` first; if that page is missing/stub, fall back to parsing
`<tool> --help` (and subcommand `--help` for multi-command tools like `docker`
and `gobuster`). Record which source each item came from — useful for
sanity-checking later.

**Base image recommendation:** use `kalilinux/kali-rolling` rather than plain
Debian/Ubuntu. It's the one base where `hydra`, `gobuster`, `hashcat`, `tcpdump`,
`smbclient`, `nmap`, and `curl` are all first-class packages with real man pages,
which avoids fighting apt repo availability across 9 different tools. `docker`
CLI (just the client, not the daemon) may need Docker's own apt repo added, or
can fall back to `--help` parsing if the man page isn't worth the extra repo.
Verify package names/availability at build time; this is a reasonable default,
not a hard requirement.

**Windows note:** this requires Docker Desktop set to **Linux containers**
(the default mode, backed by WSL2) — not Windows containers. Worth a one-line
callout in the README Claude Code generates, since it's an easy thing to trip
on if Docker Desktop was ever switched modes for something else.

## 5. Architecture

```
cli-drill/
├── Dockerfile              # installs man-db + the 9 tools, runs the generator at build time
├── docker-compose.yml      # one service, binds 127.0.0.1:<port>->8080, no other services needed
├── build/
│   └── generate_items.py   # parses man pages (or --help) into structured JSON — runs at BUILD time
├── app/
│   ├── index.html          # quiz UI shell + styles
│   ├── app.js               # quiz engine: modes, filtering, leitner buckets, localStorage
│   ├── curated-scenarios.js # hand-authored "build the full command" + HTTP-syntax items
│   └── generated-items.json # OUTPUT of generate_items.py, baked into the image, served statically
└── server/
    └── (minimal static file server — e.g. a one-file Python http.server
         or a tiny Express static server; no real backend logic needed since
         everything is pre-generated at build time)
```

**Why generate at build time, not runtime:** the man pages don't change once
the image is built, so there's no reason to parse them on every container
start. Build-time generation means faster startup and a container that truly
never needs network access to function.

**To refresh content later** (add a tool, pick up an updated package version):
edit the tool list in the Dockerfile/generator config and rebuild
(`docker compose build --no-cache`). This is the intended "update" workflow —
no live-refresh feature needed in the app itself.

## 6. Man Page → Quiz Item Pipeline (`generate_items.py`)
1. For each tool in the config list, capture plain text: `MANWIDTH=80 man <tool>
   | col -bx` (strips formatting/backspaces), or the `--help` fallback per §4.
2. Isolate the OPTIONS/flags section with a heuristic parser: a line matching a
   flag pattern (`-x`, `--long-flag`, `-x, --long-flag <arg>`) starts a new
   entry; subsequent indented lines until the next flag pattern are its
   description.
3. Emit one JSON object per flag:
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
4. Write all entries to `app/generated-items.json`.
5. Don't try to be clever about deduplicating or rewriting descriptions — keep
   `raw_excerpt` close to the source text so if something reads oddly, it's
   traceable back to the actual man page, not a parsing artifact pretending to
   be authoritative.
6. Expect the parser to be imperfect on some tools' formatting (man pages are
   not a clean structured format) — a few malformed entries are an acceptable
   v1 trade-off versus hand-typing everything. A quick manual glance through
   `generated-items.json` after first build is worth doing.

## 7. Data Model — Curated Layer (`curated-scenarios.js`)
Separate from generated content, hand-maintained, small and high-value:
```js
const CURATED_ITEMS = [
  {
    id: "nmap-scenario-001",
    tool: "nmap",
    category: "scenario",
    prompt: "SYN scan, top 1000 ports, skip host discovery, verbose",
    answer: "nmap -sS -Pn -v <target>"
  },
  {
    id: "http-001",
    tool: "http",
    category: "http-syntax",
    prompt: "Format of an HTTP request line",
    answer: "METHOD /path HTTP/version",
    example: "GET /api/users HTTP/1.1"
  }
];
```
Quiz engine merges `generated-items.json` + `curated-scenarios.js` at load time.

## 8. Features

### P0
- Quiz mode: prompt shown, self-graded pass/fail (don't string-match free-typed
  CLI syntax — too brittle, same reasoning as v1).
- Filter by tool and by category (`flag` / `scenario` / `http-syntax`).
- Leitner-style missed-item weighting (3 buckets: new / learning / known).
- Progress persisted via `localStorage`.
- Session summary (right/wrong count, items to revisit).
- `docker compose up` → browser at `http://127.0.0.1:<port>` → studying, no other setup.

### P1
- Flashcard/browse mode alongside quiz mode.
- Small "source" indicator on generated items (man vs `--help`) — useful trust signal.
- Optional server-side progress backup to a **named Docker volume**
  (`/data/progress.json`) rather than a bind mount to a Windows path — named
  volumes sidestep Windows/WSL2 path-translation quirks entirely. Only worth
  doing if you expect to rebuild the image often; since this isn't a persistent
  service, losing localStorage progress on a fresh `docker compose down` +
  rebuild is a reasonable v1 trade-off. Skip if it adds real complexity.

### Out of scope
- Any runtime internet access.
- Actually executing any of the 9 tools.
- Public/remote hosting, auth, multi-user.

## 9. Acceptance Criteria
- [ ] `docker compose up --build` produces a working container with no network
      access needed after the image is built.
- [ ] Visiting `http://127.0.0.1:<port>` shows a working quiz drawing from all
      9 tools plus curated scenario/HTTP items.
- [ ] `generated-items.json` contains real flag text traceable to actual man
      pages (or `--help` output) for each tool — spot-check a few entries
      against `man nmap` etc. on first build.
- [ ] Wrong answers reappear more often within a session/across sessions.
- [ ] Adding a new tool = one line in the generator's tool list + rebuild —
      no other code changes required.
- [ ] Adding a new curated scenario/HTTP item = one object in
      `curated-scenarios.js`.

## 10. Handoff Notes for Claude Code
- Target environment is **Windows 11 + Docker Desktop (Linux containers mode)**,
  run as a spin-up/study/tear-down tool via `docker compose up` /
  `docker compose down` — not deployed anywhere persistent, not part of the
  Proxmox homelab. Keep setup to standard `docker compose` commands only;
  don't assume a reverse proxy, TLS, or any always-on infrastructure.
- Keep the container single-purpose: build-time tool install + man-page parse,
  runtime = static file serving only. Resist adding a database or real backend —
  everything the app needs is a pre-generated JSON file.
- Bind the compose service to `127.0.0.1` by default, not `0.0.0.0` — no reason
  for this to be reachable from anywhere but this device.
- If a tool's man page turns out to be unavailable or garbage on the chosen base
  image, fall back to `--help` parsing rather than skipping the tool or
  hand-typing a substitute — keep the "sourced from the real tool" guarantee intact.
- It's fine if the first build's parser output is a little messy — flag that as
  a known v1 limitation rather than over-engineering the parser before seeing
  real output.
