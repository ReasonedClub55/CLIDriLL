/** Shared helpers used by deck-list.js, quiz.js, flashcards.js, app.js. */

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
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
