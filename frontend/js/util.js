/** Shared helpers used by deck-list.js, quiz.js, flashcards.js, app.js. */

const _HTML_ESCAPES = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };

// Escapes text for safe interpolation into both HTML text nodes and
// double-quoted HTML attributes -- callers embed this in `attr="${...}"`
// throughout quiz.js/authoring.js, so quotes must be escaped too.
function escapeHtml(str) {
  return (str == null ? "" : String(str)).replace(/[&<>"']/g, (ch) => _HTML_ESCAPES[ch]);
}

function normalizeAnswer(str) {
  return str.trim().toLowerCase().replace(/\s+/g, " ");
}

// Convenience default for the "slug" field on the new-deck form -- not a
// validation rule (the server's SLUG_RE + 409-on-duplicate is what actually
// gates a deck slug); this just saves typing a sensible one by hand.
function slugify(str) {
  return str
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}
