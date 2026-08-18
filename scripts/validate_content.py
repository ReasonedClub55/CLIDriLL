#!/usr/bin/env python3
"""CLI wrapper: validate content/decks/*.json using app/content_validation.py.

Usage:
    python scripts/validate_content.py [path ...]

With no arguments, validates every *.json file in content/decks/.
Exits non-zero if any file fails validation.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.content_validation import ContentValidationError, validate_deck_file  # noqa: E402

DEFAULT_DECKS_DIR = REPO_ROOT / "content" / "decks"


def main(argv: list[str]) -> int:
    if argv:
        paths = [Path(p) for p in argv]
    else:
        paths = sorted(DEFAULT_DECKS_DIR.glob("*.json"))

    if not paths:
        print(f"No deck JSON files found under {DEFAULT_DECKS_DIR}")
        return 1

    ok = 0
    failed = 0
    for path in paths:
        try:
            deck = validate_deck_file(path)
        except ContentValidationError as exc:
            print(f"FAIL {exc.path}\n  {exc.message}")
            failed += 1
        else:
            print(f"OK   {path}  ({len(deck.questions)} questions)")
            ok += 1

    print(f"\n{ok} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
