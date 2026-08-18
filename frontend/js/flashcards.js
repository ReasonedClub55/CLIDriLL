/** Flashcard/browse mode: click-to-flip navigation through a deck's
 * questions. Purely read-only browsing -- no grading, no progress writes. */

async function renderFlashcards(container, deckId) {
  container.innerHTML = "<p>Loading…</p>";
  const deck = await api.getDeck(deckId);
  if (!deck.questions || deck.questions.length === 0) {
    container.innerHTML = `
      <p>${escapeHtml(deck.title)} has no questions yet.</p>
      <p><a href="#/decks">Back to decks</a></p>
    `;
    return;
  }

  const state = { deck, index: 0, revealed: false };
  renderFlashcard(container, state);
}

function renderFlashcard(container, state) {
  const question = state.deck.questions[state.index];
  const isFirst = state.index === 0;
  const isLast = state.index === state.deck.questions.length - 1;

  const back = state.revealed
    ? `
        <p class="answer">${escapeHtml(question.answer)}</p>
        ${question.example ? `<p class="example">${escapeHtml(question.example)}</p>` : ""}
      `
    : `<p class="hint">Click the card to reveal the answer</p>`;

  container.innerHTML = `
    <div class="flashcards">
      <h1>${escapeHtml(state.deck.title)}</h1>
      <p class="flashcard-progress">${state.index + 1} / ${state.deck.questions.length}</p>
      <div class="flashcard" id="flashcard">
        <p class="prompt">${escapeHtml(question.prompt)}</p>
        <hr />
        ${back}
      </div>
      <div class="flashcard-nav">
        <button type="button" class="button secondary" id="prev" ${isFirst ? "disabled" : ""}>Previous</button>
        <button type="button" class="button secondary" id="next" ${isLast ? "disabled" : ""}>Next</button>
      </div>
      <p><a href="#/decks">Back to decks</a></p>
    </div>
  `;

  container.querySelector("#flashcard").addEventListener("click", () => {
    state.revealed = !state.revealed;
    renderFlashcard(container, state);
  });
  container.querySelector("#prev").addEventListener("click", () => {
    state.index = Math.max(0, state.index - 1);
    state.revealed = false;
    renderFlashcard(container, state);
  });
  container.querySelector("#next").addEventListener("click", () => {
    state.index = Math.min(state.deck.questions.length - 1, state.index + 1);
    state.revealed = false;
    renderFlashcard(container, state);
  });
}
