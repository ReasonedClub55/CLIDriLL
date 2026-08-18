# PRD: CLI Flag & Syntax Drill Tool

## 1. Problem Statement
I keep forgetting the exact flags, flag combinations, and syntax for command-line
tools I use in security work (starting with `curl` and `nmap`), plus the raw
syntax of HTTP requests (request line, headers, methods). I need a lightweight,
free, local drilling tool — not a reference page I passively read, but something
that actively quizzes me until the flags stick.

## 2. Goals
- Drill recall of CLI flags/options for security tools, starting with `curl` and `nmap`.
- Drill raw HTTP request syntax (methods, headers, request-line format, status codes).
- Support building up *full commands* from a scenario, not just single flags in isolation
  (e.g. "SYN scan, top 1000 ports, no ping, verbose" → `nmap -sS -Pn -v <target>`).
- Track which items I get wrong repeatedly so they show up more often (basic spaced repetition).
- Zero cost, zero hosting, zero accounts. Runs by opening a file in a browser.
- Easy for me (or Claude Code later) to add new tools/flags without touching app logic.

## 3. Non-Goals
- No backend, no server, no build step, no npm install.
- No user accounts, no cloud sync, no payment/subscription anything.
- No mobile app — desktop browser only.
- Not trying to cover every tool on day one — architecture should make adding
  tools (gobuster, hydra, netcat, tcpdump filters, hashcat, msfconsole, ssh, smbclient)
  trivial later, but initial content is just `curl`, `nmap`, and HTTP syntax.

## 4. User
Just me. Single-user, local, no multi-profile support needed.

## 5. Data Model
Content lives in a plain JS/JSON data file, separate from app logic, so it's easy
to extend without touching the quiz engine.

```js
// data.js
const DRILL_ITEMS = [
  {
    id: "curl-001",
    tool: "curl",
    category: "flag",           // "flag" | "http-syntax" | "scenario"
    prompt: "Flag to follow HTTP redirects",
    answer: "-L, --location",
    example: "curl -L https://example.com",
    tags: ["redirects", "basics"]
  },
  {
    id: "http-001",
    tool: "http",
    category: "http-syntax",
    prompt: "Format of an HTTP request line",
    answer: "METHOD /path HTTP/version",
    example: "GET /api/users HTTP/1.1",
    tags: ["request-line"]
  },
  {
    id: "nmap-scenario-001",
    tool: "nmap",
    category: "scenario",
    prompt: "SYN scan, top 1000 ports, skip host discovery, verbose output",
    answer: "nmap -sS -Pn -v <target>",
    tags: ["scan-type", "host-discovery"]
  }
];
```

Every item needs: `id`, `tool`, `category`, `prompt`, `answer`. `example` and `tags`
are optional but preferred. `category: "scenario"` items are the "construct the
full command" drills — these matter more than single-flag recall since that's
closer to how it's actually used.

## 6. Features

### P0 (must have for v1)
- **Quiz mode**: shows a prompt (flag description or scenario), user types or
  reveals the answer, self-grades right/wrong (Pass/Fail buttons — don't try to
  string-match free-text CLI syntax, it's too brittle).
- **Flashcard mode**: flip-card style, no grading, just browse.
- **Filter by tool**: study only `curl`, only `nmap`, only HTTP syntax, or mixed.
- **Missed-item weighting**: wrong answers get queued to reappear sooner
  (simple leitner-box style: 3 buckets — new/learning/known — is enough, no
  need for full SM-2 spaced repetition algorithm).
- **Progress persistence**: use `localStorage` so progress survives closing the
  browser tab. No backend needed for this.
- **Session summary**: at the end of a round, show right/wrong count and which
  items to revisit.

### P1 (nice to have, skip if it adds complexity)
- Toggle between "flag → description" and "description → flag" quiz direction.
- "Command construction" mode as a distinct quiz type from single-flag recall,
  since scenario-building is the harder skill.
- Simple stats view: accuracy by tool, weakest tags.

### Explicitly out of scope for v1
- Timed drills / typing speed tests.
- Import/export of progress (just keep it in localStorage; if it resets, it resets).
- Any kind of auto-generated content — all drill items are hand-authored data.

## 7. Tech Stack & Architecture
- Plain HTML + vanilla JavaScript. No frameworks, no bundler, no build step.
- Two files:
  - `index.html` — app shell, quiz engine, UI logic, inline `<style>`.
  - `data.js` — the `DRILL_ITEMS` array, loaded via `<script src="data.js">`
    before the app script. This is the file that grows over time as I add tools.
- Open `index.html` directly in a browser (`file://`) — no local server required,
  so avoid any fetch() calls to load data.js; it must be a plain script include.
- Dark, terminal-ish visual style fits the subject matter but isn't a hard requirement.

## 8. File Structure
```
cli-drill/
├── index.html   # app shell + quiz logic + styles
└── data.js      # DRILL_ITEMS content array (edit this to add content)
```

## 9. Initial Content Scope (v1 seed data)
Claude Code should seed `data.js` with a reasonable starting set, not an
exhaustive one — I'll grow it over time:
- **curl**: ~20-25 core flags (`-X`, `-H`, `-d`/`--data`, `-L`, `-I`, `-o`/`-O`,
  `-v`, `-s`, `-k`, `-u`, `-b`/`-c` (cookies), `--data-urlencode`, `-F` (multipart),
  auth flags, proxy flags).
- **nmap**: ~20-25 core flags (scan types `-sS -sT -sU -sV -sC`, timing `-T0`-`T5`,
  `-Pn`, `-p`, `-O`, `-A`, `-v`/`-vv`, output flags `-oN -oX -oG`, `--script`).
- **HTTP syntax**: request line format, common methods (GET/POST/PUT/DELETE/PATCH/HEAD/OPTIONS),
  common headers (Host, Content-Type, Authorization, Cookie, User-Agent), status
  code ranges (1xx-5xx meanings), request vs response structure.
- A handful (5-10) of `nmap` and `curl` **scenario** items combining multiple flags,
  since that's the actual target skill.

## 10. UX Notes
- Single page, no routing needed.
- Big, uncluttered quiz card in the center; tool filter and mode toggle up top.
- Keyboard-friendly: space/enter to reveal answer, arrow keys or 1/2 to grade pass/fail.
- Should feel fast to open and immediately start drilling — no setup screens.

## 11. Acceptance Criteria
- [ ] Opening `index.html` directly (double-click, `file://`) works with no server.
- [ ] Can filter to just curl, just nmap, just HTTP syntax, or all combined.
- [ ] Wrong answers reliably reappear more often than correct ones in the same or next session.
- [ ] Progress (bucket state per item) survives a browser refresh via localStorage.
- [ ] Adding a new drill item is just adding one object to the `DRILL_ITEMS` array —
      no changes needed elsewhere.

## 12. Handoff Notes for Claude Code
- Keep it to the two files described above; resist the urge to add a build step
  or extra dependencies.
- Prioritize getting quiz mode + missed-item weighting + localStorage persistence
  working correctly over visual polish.
- Seed data.js generously enough to be useful on day one (see section 9) but treat
  it as a starting point I'll keep extending, not a finished dataset.
