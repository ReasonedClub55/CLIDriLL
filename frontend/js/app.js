/** Tiny hash router wiring deck-list.js / quiz.js / flashcards.js into the
 * single #app container. No build step, no framework -- plain scripts. */

const appEl = document.getElementById("app");

function parseRoute() {
  const hash = window.location.hash.replace(/^#\/?/, "");
  return hash.split("/").filter(Boolean);
}

async function router() {
  const [view, id] = parseRoute();
  try {
    if (!view || view === "decks") {
      await renderDeckList(appEl);
    } else if (view === "study" && id) {
      await renderQuiz(appEl, Number(id));
    } else if (view === "flashcards" && id) {
      await renderFlashcards(appEl, Number(id));
    } else {
      appEl.innerHTML = '<p>Not found. <a href="#/decks">Back to decks</a></p>';
    }
  } catch (err) {
    appEl.innerHTML = `<p class="error">Error: ${escapeHtml(err.message)}</p>`;
  }
}

// A link back to the hash we're already on (e.g. "Study again" after
// finishing a session) doesn't fire 'hashchange', so re-run the router
// manually in that case instead of relying only on the event below.
document.addEventListener("click", (event) => {
  const link = event.target.closest("a[href^='#/']");
  if (!link) return;
  if (link.getAttribute("href") === window.location.hash) {
    event.preventDefault();
    router();
  }
});

window.addEventListener("hashchange", router);
window.addEventListener("DOMContentLoaded", router);
