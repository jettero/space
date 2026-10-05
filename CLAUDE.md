# Code preferences

## Style
- `black -l 127` on every python file touched (pre-commit enforces it).
- Shorter is better. Don't spend 40 lines on what 5 can do.
- Walrus where it fits: `if m := something`.
- DRY. Reuse existing helpers, constants, and library built-ins before writing new ones.
- Public names by default; `_private` only when truly internal. No leading underscore on module-level tables/constants others might use.
- Match the surrounding style.
- Imports at top: stdlib, third-party, then `space`. Break only to dodge a circular import.

## Don't
- No comments unless asked. Keep mine unless the code makes them false.
- No `getattr`/`hasattr` unless asked.
- No `try`/`except` unless asked.
- Don't re-check a type or method the context already guarantees (after `isinstance`, a logging filter's `record.msg`, `logging.root.handlers`…).
- No single-use temporaries you introduce (`me = objs.me`, `v`, `tmp`, `res`, `buf`). Inline them; bind only to avoid recomputing something expensive. Never remove single-use names I wrote.

## Behavior
- Client-facing apps: ^D/EOF exits cleanly; quit/exit work too.
- Anything persistent: ^C/KeyboardInterrupt → clean immediate exit. Always handle it.

## Docstrings
- A short plain document: what it does, inputs, key behaviors (scoring, filtering, side effects). Multi-paragraph when needed.
- Wrap ~70–80 cols; triple quotes on their own lines; blank line before the body.
- Annotate documented functions. Variable signatures → `A | B`, not `@overload`.

## Tests
- Fixtures, never generator functions (`vroom`, not `gen_vroom()`). Ad-hoc debugging → a minimal test, not inline python.
- Run new/relevant tests first, then plain `pytest` (no Makefile). On failure read `last-test-run.log`; pytest writes it, never append to it.
