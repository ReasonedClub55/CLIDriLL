# Frontend regressions

From the repository root, with Node.js 18 or later:

```bash
node --test tests/frontend/*.test.cjs
```

These tests run the existing browser scripts with small DOM and API stand-ins.
They require no npm packages and are separate from `pytest tests/`. They check
the save/export/editor workflow; they do not replace a browser smoke test.
