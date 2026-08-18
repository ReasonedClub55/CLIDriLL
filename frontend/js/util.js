/** Shared helpers used by deck-list.js, quiz.js, flashcards.js, app.js. */

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : String(str);
  return div.innerHTML;
}

function normalizeAnswer(str) {
  return str.trim().toLowerCase().replace(/\s+/g, " ");
}
