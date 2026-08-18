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
      detail = body.detail || detail;
    } catch {
      // response wasn't JSON; fall back to statusText
    }
    throw new Error(`${resp.status} ${detail}`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}

const api = {
  listDecks: () => apiRequest("/decks"),
  getDeck: (deckId) => apiRequest(`/decks/${deckId}`),
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
