/** Thin fetch wrapper around the FastAPI backend. The frontend never talks
 * to the database directly -- everything goes through /api/*. */

const API_BASE = "/api";

async function apiRequest(path, options = {}) {
  const resp = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = formatDetail(body.detail) || detail;
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new Error(`${resp.status} ${detail}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

// FastAPI sends HTTPException details as a string but request-validation
// (422) details as a list of {loc, msg} objects; flatten the latter so the
// message names the offending field (e.g. "body.questions.3.answer: ...")
// instead of "[object Object]".
function formatDetail(detail) {
  if (!Array.isArray(detail)) return detail;
  return detail
    .map((d) => (Array.isArray(d.loc) ? `${d.loc.join(".")}: ${d.msg}` : String(d.msg ?? d)))
    .join("; ");
}

const api = {
  listDecks: () => apiRequest("/decks"),
  getDeck: (deckId) => apiRequest(`/decks/${deckId}`),
  createDeck: (payload) =>
    apiRequest("/decks", { method: "POST", body: JSON.stringify(payload) }),
  updateDeck: (deckId, payload) =>
    apiRequest(`/decks/${deckId}`, { method: "PATCH", body: JSON.stringify(payload) }),
  deleteDeck: (deckId) => apiRequest(`/decks/${deckId}`, { method: "DELETE" }),
  importDeck: (deckFile) =>
    apiRequest("/decks/import", { method: "POST", body: JSON.stringify(deckFile) }),
  createQuestion: (deckId, payload) =>
    apiRequest(`/decks/${deckId}/questions`, {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateQuestion: (deckId, questionId, payload) =>
    apiRequest(`/decks/${deckId}/questions/${questionId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
  deleteQuestion: (deckId, questionId) =>
    apiRequest(`/decks/${deckId}/questions/${questionId}`, { method: "DELETE" }),
  startSession: (deckId) =>
    apiRequest("/study/sessions", {
      method: "POST",
      body: JSON.stringify({ deck_id: deckId }),
    }),
  nextQuestion: (sessionId) => apiRequest(`/study/sessions/${sessionId}/next`),
  submitAnswer: (sessionId, questionId, correct) =>
    apiRequest(`/study/sessions/${sessionId}/answer`, {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, correct }),
    }),
  finishSession: (sessionId) =>
    apiRequest(`/study/sessions/${sessionId}/finish`, { method: "POST" }),
};
