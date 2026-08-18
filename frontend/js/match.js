/** Match-style study mode (#/match/:id, plan.md issue 15, P2 stretch):
 * click a prompt tile then its matching answer tile to pair them off
 * against the clock. This is ungraded practice, deliberately not wired
 * into the Leitner/Progress system that quiz mode drives -- there's no
 * single "correct/incorrect" moment to report per question the way
 * quiz mode has, so it stays a separate, simpler study aid. */

const MATCH_ROUND_SIZE = 8;
const MATCH_MIN_QUESTIONS = 4;

async function renderMatch(container, deckId) {
  container.innerHTML = "<p>Loading…</p>";
  const deck = await api.getDeck(deckId);
  if (!deck.questions || deck.questions.length < MATCH_MIN_QUESTIONS) {
    container.innerHTML = `
      <p>${escapeHtml(deck.title)} needs at least ${MATCH_MIN_QUESTIONS} questions for
      match mode (has ${deck.questions ? deck.questions.length : 0}).</p>
      <p><a href="#/decks">Back to decks</a></p>
    `;
    return;
  }
  startMatchRound(container, deck);
}

function shuffle(items) {
  const copy = items.slice();
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

function startMatchRound(container, deck) {
  const pool = shuffle(deck.questions).slice(0, Math.min(MATCH_ROUND_SIZE, deck.questions.length));
  const state = {
    deck,
    matchedIds: new Set(),
    prompts: shuffle(pool.map((q) => ({ id: q.id, text: q.prompt }))),
    answers: shuffle(pool.map((q) => ({ id: q.id, text: q.answer }))),
    selectedPromptTile: null,
    selectedAnswerTile: null,
    selectedPromptId: null,
    selectedAnswerId: null,
    startedAt: Date.now(),
    timerId: null,
  };

  renderMatchBoard(container, state);
  state.timerId = setInterval(() => updateMatchTimer(container, state), 1000);
}

function renderMatchBoard(container, state) {
  container.innerHTML = `
    <div class="quiz-header">
      <h1>${escapeHtml(state.deck.title)} — Match</h1>
      <div class="quiz-score" id="match-timer">${formatElapsed(state)}</div>
      <a class="button secondary" href="#/decks">End</a>
    </div>
    <div class="match-board">
      <div class="match-column">
        ${state.prompts.map((p) => matchTileHtml(p, "prompt")).join("")}
      </div>
      <div class="match-column">
        ${state.answers.map((a) => matchTileHtml(a, "answer")).join("")}
      </div>
    </div>
  `;
  wireMatchHandlers(container, state);
}

function matchTileHtml(item, side) {
  return `
    <button type="button" class="match-tile" data-side="${side}" data-id="${item.id}">
      ${escapeHtml(item.text)}
    </button>
  `;
}

function wireMatchHandlers(container, state) {
  container.querySelectorAll(".match-tile").forEach((tile) => {
    tile.addEventListener("click", () => handleMatchTileClick(container, state, tile));
  });
}

function handleMatchTileClick(container, state, tile) {
  if (tile.disabled) return;
  const side = tile.dataset.side;
  const id = Number(tile.dataset.id);

  if (side === "prompt") {
    if (state.selectedPromptTile) state.selectedPromptTile.classList.remove("selected");
    tile.classList.add("selected");
    state.selectedPromptTile = tile;
    state.selectedPromptId = id;
  } else {
    if (state.selectedAnswerTile) state.selectedAnswerTile.classList.remove("selected");
    tile.classList.add("selected");
    state.selectedAnswerTile = tile;
    state.selectedAnswerId = id;
  }

  if (state.selectedPromptId != null && state.selectedAnswerId != null) {
    evaluateMatchSelection(container, state);
  }
}

function evaluateMatchSelection(container, state) {
  const promptTile = state.selectedPromptTile;
  const answerTile = state.selectedAnswerTile;
  const isMatch = state.selectedPromptId === state.selectedAnswerId;

  if (isMatch) {
    state.matchedIds.add(state.selectedPromptId);
    [promptTile, answerTile].forEach((tile) => {
      tile.classList.remove("selected");
      tile.classList.add("matched");
      tile.disabled = true;
    });
    clearMatchSelection(state);

    if (state.matchedIds.size === state.prompts.length) {
      clearInterval(state.timerId);
      setTimeout(() => renderMatchComplete(container, state), 400);
    }
  } else {
    promptTile.classList.add("wrong");
    answerTile.classList.add("wrong");
    setTimeout(() => {
      promptTile.classList.remove("selected", "wrong");
      answerTile.classList.remove("selected", "wrong");
    }, 500);
    clearMatchSelection(state);
  }
}

function clearMatchSelection(state) {
  state.selectedPromptTile = null;
  state.selectedAnswerTile = null;
  state.selectedPromptId = null;
  state.selectedAnswerId = null;
}

function formatElapsed(state) {
  const seconds = Math.floor((Date.now() - state.startedAt) / 1000);
  const m = String(Math.floor(seconds / 60)).padStart(2, "0");
  const s = String(seconds % 60).padStart(2, "0");
  return `${m}:${s}`;
}

function updateMatchTimer(container, state) {
  const el = container.querySelector("#match-timer");
  if (!el) {
    // Navigated away from the match view -- stop ticking.
    clearInterval(state.timerId);
    return;
  }
  el.textContent = formatElapsed(state);
}

function renderMatchComplete(container, state) {
  container.innerHTML = `
    <div class="summary">
      <h1>All matched!</h1>
      <p>${escapeHtml(state.deck.title)}</p>
      <p class="summary-stats">Time: ${formatElapsed(state)}</p>
      <div class="summary-actions">
        <a class="button" href="#/match/${state.deck.id}">Play again</a>
        <a class="button secondary" href="#/decks">Back to decks</a>
      </div>
    </div>
  `;
}
