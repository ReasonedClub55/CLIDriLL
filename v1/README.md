# v1 — plain HTML edition

No build step, no server, no dependencies. Open `index.html` directly via `file://`.

Planned files (not yet implemented — see [`../docs/prd-v1-html.md`](../docs/prd-v1-html.md)):
- `index.html` — app shell, quiz engine, UI logic, inline styles
- `data.js` — `DRILL_ITEMS` seed array, loaded via a plain `<script>` tag (no `fetch()`)
