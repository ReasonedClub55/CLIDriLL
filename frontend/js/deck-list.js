/** Deck list page: the app's home view. */

async function renderDeckList(container) {
  container.innerHTML = "<p>Loading decks…</p>";
  const decks = await api.listDecks();

  if (decks.length === 0) {
    container.innerHTML = "<p>No decks yet.</p>";
    return;
  }

  container.innerHTML = `
    <h1>Decks</h1>
    <div class="deck-grid">
      ${decks.map(deckCardHtml).join("")}
    </div>
  `;
}

function deckCardHtml(deck) {
  return `
    <article class="deck-card">
      <h2>${escapeHtml(deck.title)}</h2>
      <p class="deck-description">${escapeHtml(deck.description || "")}</p>
      <div class="deck-card-actions">
        <a class="button" href="#/study/${deck.id}">Study</a>
        <a class="button secondary" href="#/flashcards/${deck.id}">Flashcards</a>
      </div>
    </article>
  `;
}
