/** Study/quiz mode: cycles Leitner-weighted questions from the backend and
 * renders one of three per-type layouts (multiple_choice / short_answer /
 * free_response), grading client-side against the answer the API already
 * returned, then reports correct/incorrect back to /api/study so the
 * server-side Progress bucket and session counters advance. */

async function renderQuiz(container, deckId) {
  container.innerHTML = "<p>Loading…</p>";
  const deck = await api.getDeck(deckId);
  if (!deck.questions || deck.questions.length === 0) {
    container.innerHTML = emptyDeckHtml(deck);
    return;
  }

  const session = await api.startSession(deckId);
  const state = { deck, session, correct: 0, wrong: 0 };
  await loadNextQuestion(container, state);
}

function emptyDeckHtml(deck) {
  return `
    <p>${escapeHtml(deck.title)} has no questions yet.</p>
    <p><a href="#/decks">Back to decks</a></p>
  `;
}

async function loadNextQuestion(container, state) {
  const question = await api.nextQuestion(state.session.id);
  if (!question) {
    renderQuizSummary(container, state);
    return;
  }
  state.question = question;
  container.innerHTML = quizHeaderHtml(state) + questionHtml(question);
  wireQuestionHandlers(container, state);
}

function quizHeaderHtml(state) {
  return `
    <div class="quiz-header">
      <h1>${escapeHtml(state.deck.title)}</h1>
      <div class="quiz-score">${state.correct} correct &middot; ${state.wrong} wrong</div>
      <button type="button" class="button secondary" id="end-session">End session</button>
    </div>
  `;
}

function questionHtml(question) {
  const promptHtml = `<p class="prompt">${escapeHtml(question.prompt)}</p>`;

  if (question.type === "multiple_choice") {
    const choicesHtml = question.choices
      .map(
        (choice) =>
          `<button type="button" class="choice" data-choice="${escapeHtml(choice)}">${escapeHtml(choice)}</button>`
      )
      .join("");
    return `
      <div class="question">
        ${promptHtml}
        <div class="choices">${choicesHtml}</div>
        <div class="feedback" id="feedback"></div>
      </div>
    `;
  }

  if (question.type === "short_answer") {
    return `
      <div class="question">
        ${promptHtml}
        <form id="answer-form">
          <input type="text" id="answer-input" autocomplete="off" placeholder="Your answer" />
          <button type="submit" class="button">Check</button>
        </form>
        <div class="feedback" id="feedback"></div>
      </div>
    `;
  }

  // free_response: self-graded, since a brittle string match doesn't work
  // for scenario/command-construction items (plan.md §6).
  return `
    <div class="question">
      ${promptHtml}
      <button type="button" class="button" id="reveal">Reveal answer</button>
      <div class="answer-reveal" id="answer-reveal" hidden>
        <p class="answer">${escapeHtml(question.answer)}</p>
        <div class="self-grade">
          <button type="button" class="button" data-correct="true">I got it right</button>
          <button type="button" class="button secondary" data-correct="false">I got it wrong</button>
        </div>
      </div>
      <div class="feedback" id="feedback"></div>
    </div>
  `;
}

function wireQuestionHandlers(container, state) {
  container.querySelector("#end-session").addEventListener("click", async () => {
    await api.finishSession(state.session.id);
    renderQuizSummary(container, state);
  });

  const question = state.question;

  if (question.type === "multiple_choice") {
    container.querySelectorAll(".choice").forEach((btn) => {
      btn.addEventListener("click", () => {
        const correct = btn.dataset.choice === question.answer;
        gradeAndAdvance(container, state, correct);
      });
    });
  } else if (question.type === "short_answer") {
    container.querySelector("#answer-form").addEventListener("submit", (event) => {
      event.preventDefault();
      const input = container.querySelector("#answer-input").value;
      const correct = normalizeAnswer(input) === normalizeAnswer(question.answer);
      gradeAndAdvance(container, state, correct);
    });
  } else {
    container.querySelector("#reveal").addEventListener("click", () => {
      container.querySelector("#reveal").hidden = true;
      container.querySelector("#answer-reveal").hidden = false;
    });
    container.querySelectorAll("[data-correct]").forEach((btn) => {
      btn.addEventListener("click", () => {
        gradeAndAdvance(container, state, btn.dataset.correct === "true");
      });
    });
  }
}

async function gradeAndAdvance(container, state, correct) {
  const feedback = container.querySelector("#feedback");
  feedback.textContent = correct ? "Correct!" : `Not quite — answer: ${state.question.answer}`;
  feedback.className = `feedback ${correct ? "correct" : "wrong"}`;
  container.querySelectorAll("button, input").forEach((el) => {
    el.disabled = true;
  });

  await api.submitAnswer(state.session.id, state.question.id, correct);
  if (correct) {
    state.correct += 1;
  } else {
    state.wrong += 1;
  }

  setTimeout(() => loadNextQuestion(container, state), 900);
}

function renderQuizSummary(container, state) {
  const total = state.correct + state.wrong;
  const accuracy = total ? Math.round((state.correct / total) * 100) : 0;
  container.innerHTML = `
    <div class="summary">
      <h1>Session complete</h1>
      <p>${escapeHtml(state.deck.title)}</p>
      <p class="summary-stats">
        ${state.correct} correct &middot; ${state.wrong} wrong &middot; ${accuracy}% accuracy
      </p>
      <div class="summary-actions">
        <a class="button" href="#/study/${state.deck.id}">Study again</a>
        <a class="button secondary" href="#/decks">Back to decks</a>
      </div>
    </div>
  `;
}
