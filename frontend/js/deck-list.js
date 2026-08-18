/** Deck list page: the app's home view. */

async function renderDeckList(container) {
  container.innerHTML = "<p>Loading decks…</p>";
  const decks = await api.listDecks();

  container.innerHTML = `
    <div class="page-header">
      <h1>Decks</h1>
      <div class="page-header-actions">
        <label class="button secondary file-button">
          Import JSON
          <input type="file" id="import-deck-file" accept="application/json" hidden />
        </label>
        <button type="button" class="button" id="new-deck-toggle">+ New deck</button>
      </div>
    </div>
    <p class="form-feedback" id="import-feedback"></p>
    ${newDeckFormHtml()}
    ${decks.length ? `<div class="deck-grid">${decks.map(deckCardHtml).join("")}</div>` : "<p>No decks yet.</p>"}
  `;
  wireDeckListHandlers(container);
  wireImportHandler(container);
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

// Imports a content/decks/<slug>.json-shaped file (same shape
// exportDeckJson in authoring.js produces): POSTs the deck, then each
// question, one at a time. Deliberately does not pre-validate the parsed
// JSON's shape client-side -- POST /api/decks(/questions) already runs it
// through content_validation, and duplicating that here would violate
// plan.md §7's one-place-owns-the-rules design. A failure partway through
// (e.g. one bad question) leaves the deck and whatever questions already
// succeeded in place rather than rolling back -- the editor page is where
// to fix or remove them.
function wireImportHandler(container) {
  const input = container.querySelector("#import-deck-file");
  const feedback = container.querySelector("#import-feedback");

  input.addEventListener("change", async () => {
    const file = input.files[0];
    if (!file) return;
    feedback.textContent = "Importing…";
    feedback.className = "form-feedback";

    let result;
    try {
      const data = JSON.parse(await file.text());
      const deck = await api.createDeck({
        slug: data.slug,
        title: data.title,
        description: data.description ?? null,
        source: data.source ?? "authored",
      });
      const questions = Array.isArray(data.questions) ? data.questions : [];
      let added = 0;
      for (const question of questions) {
        await api.createQuestion(deck.id, question);
        added += 1;
      }
      result = {
        text: `Imported "${deck.title}" with ${added}/${questions.length} question(s).`,
        className: "form-feedback correct",
      };
    } catch (err) {
      result = { text: `Import failed: ${err.message}`, className: "form-feedback wrong" };
    }

    // Re-render to pick up any deck/questions the import created (even on
    // a partial failure), then show the result in the freshly-rendered
    // feedback element -- innerHTML above already replaced the old one.
    await renderDeckList(container);
    const newFeedback = container.querySelector("#import-feedback");
    newFeedback.textContent = result.text;
    newFeedback.className = result.className;
  });
}
