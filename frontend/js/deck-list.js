/** Deck list page: the app's home view. */

async function renderDeckList(container) {
  container.innerHTML = "<p>Loading decks…</p>";
  const decks = await api.listDecks();

  container.innerHTML = `
    <div class="page-header">
      <h1>Decks</h1>
      <button type="button" class="button" id="new-deck-toggle">+ New deck</button>
    </div>
    ${newDeckFormHtml()}
    ${decks.length ? `<div class="deck-grid">${decks.map(deckCardHtml).join("")}</div>` : "<p>No decks yet.</p>"}
  `;
  wireDeckListHandlers(container);
}

function newDeckFormHtml() {
  return `
    <form id="new-deck-form" class="card-form" hidden>
      <label>Title <input type="text" id="new-deck-title" required /></label>
      <label>Slug <input type="text" id="new-deck-slug" placeholder="e.g. python-basics" required /></label>
      <label>Description <textarea id="new-deck-description"></textarea></label>
      <div class="form-actions">
        <button type="submit" class="button">Create deck</button>
        <button type="button" class="button secondary" id="new-deck-cancel">Cancel</button>
      </div>
      <p class="form-feedback" id="new-deck-feedback"></p>
    </form>
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
        <a class="button secondary" href="#/match/${deck.id}">Match</a>
        <a class="button secondary" href="#/decks/${deck.id}/edit">Edit</a>
      </div>
    </article>
  `;
}

function wireDeckListHandlers(container) {
  const toggleBtn = container.querySelector("#new-deck-toggle");
  const form = container.querySelector("#new-deck-form");

  toggleBtn.addEventListener("click", () => {
    form.hidden = !form.hidden;
  });

  container.querySelector("#new-deck-cancel").addEventListener("click", () => {
    form.reset();
    form.hidden = true;
  });

  const titleInput = container.querySelector("#new-deck-title");
  const slugInput = container.querySelector("#new-deck-slug");
  let slugTouched = false;
  slugInput.addEventListener("input", () => {
    slugTouched = true;
  });
  titleInput.addEventListener("input", () => {
    if (!slugTouched) slugInput.value = slugify(titleInput.value);
  });

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const feedback = container.querySelector("#new-deck-feedback");
    try {
      const deck = await api.createDeck({
        title: titleInput.value.trim(),
        slug: slugInput.value.trim(),
        description: container.querySelector("#new-deck-description").value.trim() || null,
      });
      window.location.hash = `#/decks/${deck.id}/edit`;
    } catch (err) {
      feedback.textContent = err.message;
      feedback.className = "form-feedback wrong";
    }
  });
}
