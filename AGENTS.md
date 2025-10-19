# Project Guide (Concise)

## Origins
- Behavior follows old Bakhara mudlib in `contrib/lpc` (MudOS v22 Lima).
- Port ideas, not LPC APIs. Stay Pythonic.
- For names, see `contrib/lpc/std/object/names.c`; for messages, see
  `contrib/lpc/std/modules/m_messages.c`.

## Layout
- Code: `space/` • Tests: `t/` • Config: `Makefile`, `pytest.ini`, `.pre-commit-config.yaml`, `pylintrc`.
- Artifacts: `build/`, `dist/`, `space.egg-info/`.
- Reqs: `requirements.txt` (run), `test-requirements.txt` (dev/test).

## Dev Workflow
- Run tests: `make` (uses `pytest t`). Parallelize with your CPU count.
- Lint/format: `pre-commit run --all-files` (black, pylint). Black uses `--line-length 127`.
- Build release: `python -m build` or `make build`.
- Install test deps: `pip install -Ur test-requirements.txt` or `make reqs`.

## Style
- No `getattr`/`hasattr` or comments unless explicitly allowed.
- Avoid single-use temps; use values inline unless clarity requires a local.
- Prefer small, focused functions. Classic annotations style (no `-> T`, no `A | B`).
- Names: modules `snake_case.py`; classes `CamelCase`; vars/functions `snake_case`; constants `UPPER_SNAKE`.
- Markdown: wrap ~80 cols; keep prose tight.

## Maps/Generation
- Use `Floor` for rooms, `Corridor` for halls; both subclass `Cell` and render alike.
- Walkability: check `isinstance(x, Cell)`.
- `Map.cellify_partitions()` opens short partitions as corridors.
- Color: use shared grey (`boring_color`) for floors/corridors by default.

## Testing
- Keep deterministic; no network; isolate I/O.
- Fixtures: use those in `t/conftest.py`. Map is `a_map`; objects via `objs`.
- Assertions: prefer direct, minimal checks. For parse failures: assert falsy `pstate`, `winner is None`, and check `pstate.error` when relevant.
- Parametrize exactly as specified; don’t reshape sets. Match the stated intent only.
- Naming: positive `test_open_door`; negative ends with `_fail`/`_fails`.

## Parser/Router
- Treat `space/parser.py` and `space/router.py` as high‑risk; don’t change without a task.
- Follow `PARSER.md` for `can_*`/`do_*` contract; keys from `can_*` must match `do_*` params.
- Don’t bend `space/args.py` for a single verb; align parameter names instead.

## Messaging
- Read `MESSAGES.md` before emitting output.
- Compose separately from delivery. Return `TextMessage`; deliver via `Living.tell()` and map/cell fan‑out.
- Start with tokens: `$N/$n`, `$T/$t`, `$O/$o`, `$p/$o/$r`, `$vverb`. Expand with tests.
- Follow current `Living` gender/pronouns; access attributes directly.

## Maintainer Preferences
- Prefer the smallest, test‑local fix. Add a failing test first, then make the minimal code change.
- If adjacent tests are green and only expected text differs, suspect the expectation.
- Verify pronouns, names, token defaults, and fixtures before assuming systemic issues.
- Use `assert ps` for `PState` truthiness; avoid tuple messages.

## Git Usage
- Read‑only for context: `git diff`, `git log`.
- Never run `git commit`, `git add`, or `git reset` here. Don’t use `git mv`.

## Versioning
- Version comes from `setuptools_scm` into `space/version.py`. Don’t edit it; tag releases to bump.
- For local dev, don’t install the package; run tests with `make test`.
