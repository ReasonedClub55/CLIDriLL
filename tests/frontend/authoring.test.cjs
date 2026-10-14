const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { join } = require('node:path');
const { runInNewContext } = require('node:vm');

test('saving deck metadata keeps questions available for export and editing', async () => {
  const handlers = new Map();
  const fields = {
    '#deck-title': { value: ' Updated title ' },
    '#deck-description': { value: ' Updated description ' },
    '#deck-feedback': {},
  };
  const form = { querySelector: selector => fields[selector] };
  const container = {
    querySelector: selector => ({ addEventListener: (type, handler) => handlers.set(selector, handler) }),
    querySelectorAll: () => [],
  };
  let exportedBlob;
  const link = { click() {}, remove() {} };
  const context = {
    api: { updateDeck: async (id, payload) => ({ id, slug: 'sample', source: 'authored', ...payload }) },
    Blob,
    URL: { createObjectURL: blob => { exportedBlob = blob; return 'blob:test'; }, revokeObjectURL() {} },
    document: { createElement: () => link, body: { appendChild() {} } },
  };
  for (const file of ['util.js', 'authoring.js']) {
    runInNewContext(readFileSync(join(__dirname, '../../frontend/js', file), 'utf8'), context);
  }
  const questions = [{ id: 1, type: 'short_answer', prompt: 'Flag?', answer: '--help' }];
  const state = { deck: { id: 7, slug: 'sample', title: 'Old title', source: 'authored', questions } };
  context.wireEditorHandlers(container, state);
  await handlers.get('#deck-form')({ preventDefault() {}, currentTarget: form });
  assert.equal(fields['#deck-feedback'].textContent, 'Saved.');
  assert.equal(state.deck.title, 'Updated title');
  assert.equal(state.deck.description, 'Updated description');
  assert.strictEqual(state.deck.questions, questions);
  handlers.get('#export-deck')();
  const exported = JSON.parse(await exportedBlob.text());
  assert.equal(exported.title, 'Updated title');
  assert.equal(exported.questions.length, 1);
  assert.equal(exported.questions[0].answer, '--help');
  assert.equal(exported.questions[0].id, undefined);
  assert.equal(link.download, 'sample.json');
  context.renderEditor(container, state);
  assert.match(container.innerHTML, /Updated title/);
  assert.match(container.innerHTML, /Questions \(1\)/);
  assert.match(container.innerHTML, /Flag\?/);
});
