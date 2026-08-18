/** Deck/question authoring UI (#/decks/:id/edit): edit a deck's title and
 * description, add/edit/delete its questions. Talks only through api.js --
 * this file shapes request bodies but leaves *validating* them (e.g.
 * multiple_choice needs >=2 choices) to the server's
 * content_validation.QuestionIn, per plan.md's one-place-owns-the-rules
 * design; a failed request just surfaces the API's error message. */

const QUESTION_TYPES = ["multiple_choice", "short_answer", "free_response"];

async function renderDeckEditor(container, deckId) {
  container.innerHTML = "<p>Loading…</p>";
  const deck = await api.getDeck(deckId);
  renderEditor(container, { deck, editingId: null });
}

function renderEditor(container, state) {
  const { deck } = state;
  container.innerHTML = `
    <div class="editor-header">
      <h1>Edit deck</h1>
      <a href="#/decks">Back to decks</a>
    </div>
    <form id="deck-form" class="card-form">
      <label>Title <input type="text" id="deck-title" value="${escapeHtml(deck.title)}" required /></label>
      <label>Description <textarea id="deck-description">${escapeHtml(deck.description || "")}</textarea></label>
      <div class="form-actions">
        <button type="submit" class="button">Save deck</button>
        <button type="button" class="button danger" id="delete-deck">Delete deck</button>
      </div>
      <p class="form-feedback" id="deck-feedback"></p>
    </form>

    <h2>Questions (${deck.questions.length})</h2>
    <div id="question-list">
      ${deck.questions.map((q) => questionRowHtml(q, state)).join("") || "<p>No questions yet.</p>"}
    </div>

    <h2>Add question</h2>
    ${questionFormHtml("new")}
  `;
  wireEditorHandlers(container, state);
}

function questionRowHtml(question, state) {
  if (state.editingId === question.id) {
    return `<div class="question-row editing">${questionFormHtml(question.id, question)}</div>`;
  }
  return `
    <div class="question-row">
      <div class="question-row-main">
        <span class="badge">${escapeHtml(question.type)}</span>
        <span class="question-row-prompt">${escapeHtml(question.prompt)}</span>
      </div>
      <div class="question-row-actions">
        <button type="button" class="button secondary" data-edit="${question.id}">Edit</button>
        <button type="button" class="button danger" data-delete="${question.id}">Delete</button>
      </div>
    </div>
  `;
}

function questionFormHtml(formId, question) {
  const type = question ? question.type : "multiple_choice";
  const choices = question && question.choices && question.choices.length ? question.choices : ["", ""];
  return `
    <form class="card-form question-form" data-form-id="${formId}">
      <label>Type
        <select class="q-type">
          ${QUESTION_TYPES.map(
            (t) => `<option value="${t}" ${t === type ? "selected" : ""}>${t}</option>`
          ).join("")}
        </select>
      </label>
      <label>Prompt <textarea class="q-prompt" required>${escapeHtml(question ? question.prompt : "")}</textarea></label>
      <label>Answer <input type="text" class="q-answer" value="${escapeHtml(question ? question.answer : "")}" required /></label>
      <div class="q-choices" ${type === "multiple_choice" ? "" : "hidden"}>
        <label>Choices</label>
        <div class="q-choices-list">
          ${choices.map((c) => choiceInputHtml(c)).join("")}
        </div>
        <button type="button" class="button secondary q-add-choice">+ Add choice</button>
      </div>
      <label>Example <input type="text" class="q-example" value="${escapeHtml((question && question.example) || "")}" /></label>
      <label>Tags (comma-separated) <input type="text" class="q-tags" value="${escapeHtml(question && question.tags ? question.tags.join(", ") : "")}" /></label>
      <div class="form-actions">
        <button type="submit" class="button">${question ? "Save question" : "Add question"}</button>
        ${question ? '<button type="button" class="button secondary q-cancel">Cancel</button>' : ""}
      </div>
      <p class="form-feedback"></p>
    </form>
  `;
}

function choiceInputHtml(value) {
  return `
    <div class="q-choice-item">
      <input type="text" class="q-choice-input" value="${escapeHtml(value)}" />
      <button type="button" class="button secondary q-remove-choice">&times;</button>
    </div>
  `;
}

function wireEditorHandlers(container, state) {
  container.querySelector("#deck-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const feedback = form.querySelector("#deck-feedback");
    try {
      state.deck = await api.updateDeck(state.deck.id, {
        title: form.querySelector("#deck-title").value.trim(),
        description: form.querySelector("#deck-description").value.trim() || null,
      });
      feedback.textContent = "Saved.";
      feedback.className = "form-feedback correct";
    } catch (err) {
      feedback.textContent = err.message;
      feedback.className = "form-feedback wrong";
    }
  });

  container.querySelector("#delete-deck").addEventListener("click", async () => {
    if (!confirm(`Delete "${state.deck.title}" and all its questions? This can't be undone.`)) return;
    await api.deleteDeck(state.deck.id);
    window.location.hash = "#/decks";
  });

  container.querySelectorAll("[data-edit]").forEach((btn) => {
    btn.addEventListener("click", () => {
      state.editingId = Number(btn.dataset.edit);
      renderEditor(container, state);
    });
  });

  container.querySelectorAll("[data-delete]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      if (!confirm("Delete this question?")) return;
      await api.deleteQuestion(state.deck.id, Number(btn.dataset.delete));
      state.deck = await api.getDeck(state.deck.id);
      renderEditor(container, state);
    });
  });

  container.querySelectorAll(".question-form").forEach((form) => wireQuestionForm(container, state, form));
}

function wireQuestionForm(container, state, form) {
  const formId = form.dataset.formId;
  const typeSelect = form.querySelector(".q-type");
  const choicesWrap = form.querySelector(".q-choices");
  const choicesList = form.querySelector(".q-choices-list");

  const syncChoicesVisibility = () => {
    choicesWrap.hidden = typeSelect.value !== "multiple_choice";
  };
  typeSelect.addEventListener("change", syncChoicesVisibility);

  form.querySelector(".q-add-choice").addEventListener("click", () => {
    choicesList.insertAdjacentHTML("beforeend", choiceInputHtml(""));
    wireChoiceRemoveButtons(choicesList);
  });
  wireChoiceRemoveButtons(choicesList);

  const cancelBtn = form.querySelector(".q-cancel");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      state.editingId = null;
      renderEditor(container, state);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const feedback = form.querySelector(".form-feedback");
    const payload = readQuestionForm(form);
    try {
      if (formId === "new") {
        await api.createQuestion(state.deck.id, payload);
      } else {
        await api.updateQuestion(state.deck.id, Number(formId), payload);
      }
      state.editingId = null;
      state.deck = await api.getDeck(state.deck.id);
      renderEditor(container, state);
    } catch (err) {
      feedback.textContent = err.message;
      feedback.className = "form-feedback wrong";
    }
  });
}

function wireChoiceRemoveButtons(choicesList) {
  choicesList.querySelectorAll(".q-remove-choice").forEach((btn) => {
    btn.onclick = () => {
      if (choicesList.children.length > 1) btn.closest(".q-choice-item").remove();
    };
  });
}

function readQuestionForm(form) {
  const type = form.querySelector(".q-type").value;
  const tags = form
    .querySelector(".q-tags")
    .value.split(",")
    .map((t) => t.trim())
    .filter(Boolean);

  const payload = {
    type,
    prompt: form.querySelector(".q-prompt").value.trim(),
    answer: form.querySelector(".q-answer").value.trim(),
    example: form.querySelector(".q-example").value.trim() || null,
    tags: tags.length ? tags : null,
    choices: null,
  };

  if (type === "multiple_choice") {
    payload.choices = Array.from(form.querySelectorAll(".q-choice-input"))
      .map((input) => input.value.trim())
      .filter(Boolean);
  }

  return payload;
}
