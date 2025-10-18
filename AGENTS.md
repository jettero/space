# Repository Guidelines

## side note on project origins
- if the symlink is good, `contrib/lpc` contains my old Bakhara mudlib, which is
  MudOS v22 Lima LPC
- we're trying to mimick the behaviors of the old mudlib in python, but we're
  trying to do things pythonically instead of using LPC methods.
- when in doubt about how something should work, go scan contrib/lpc for ideas.
- if we're working on `space/names.py`; be sure to check `contrib/lpc/std/object/names.c`
- working on `space/living/msg.py`; be sure to check `contrib/lpc/std/modules/m_messages.c` for ideas

## Project Structure & Module Organization
- Package code: `space/` (see `setup.cfg` and `pyproject.toml`).
- Tests: `t/` (configured via `pytest.ini:testpaths = t`).
- Build artifacts: `build/`, `dist/`, `space.egg-info/`.
- Config/tooling: `Makefile`, `pytest.ini`, `.pre-commit-config.yaml`,
  `pylintrc`.
- Requirements: `requirements.txt` (runtime), `test-requirements.txt`
  (dev/test). Markers: `reqs`, `mods`.
- after any edit of python files in this repo, be sure to run psf-black on the
  file. we're using `black --line-length 127` (per `.pre-commit-config.yaml`);
  this only counts for actual python files. ipython-startup can't be blacked
  because it has ipython shenannigans in it.

## Build, Test, and Development Commands
- `make` or `make test` — run test suite (`pytest t`).
- Parallel runs: prefer using available CPUs instead of a fixed `-j`.
  - Examples: `make test -j"$(nproc)"` (Linux), `make test -j"$(sysctl -n
    hw.ncpu)"` (macOS), or set `-j16` if you know your core count.
  - Avoid small fixed values like `-j2` on multi-core machines.
- `pre-commit run --all-files` — run linters/formatters (pylint, black, hooks).
- `python -m build` — build sdist/wheel (also via `make build`) when cutting
  releases.
- `pip install -Ur test-requirements.txt` — install test-only deps if needed
  (`make reqs`).

## Coding Style & Naming Conventions
- you're not allowed to use getattr, hasattr, or comments without explicit
  permission. You don't seem to know when to use them, so it's just irritating
  when you try. If you think you need getattr/hasattr -- scan more of the repo
  to see what you're missing. In particular, if there's a contract for a certain
  class or if you're actually checking it with isinstance(x, Whatever); then you
  know exactly what attrs are there and you don't need to getattr or hasattr at
  all.
- You may use try/except blocks in rare cases, but you should ask first because
  you probably don't actually need it.
- fucking never assign some object's attr to a variable that you only use once.
  DO NOT DO THIS:
  ```
  a = obj.something.blah.attributename
  return a # I made a stupid dumb single use variable for no reason at all
  ```
  - Strengthened: Avoid single-use variables entirely when the value can be
    returned or used inline. Prefer `return obj.attr` over `tmp = obj.attr; return tmp`.
    Only introduce a local when it improves clarity or avoids repeated expensive
    work.
- Lint: `pylint` (configured by `pylintrc`). Format: `black` (via pre-commit).
- Indentation: 4 spaces; UTF-8; Unix newlines.
- Naming: modules `snake_case.py`; classes `CamelCase`; functions/vars
  `snake_case`; constants `UPPER_SNAKE`.
- Keep modules focused; prefer small, testable functions. Type hints encouraged
  for public APIs.

### Markdown Formatting
- Wrap Markdown text at ~80 characters per line.
- Keep prose concise; avoid unnecessary verbosity.

### Map/Generator Conventions
- Floors: use `Floor` for room interiors, `Corridor` for hallways; both subclass
  `Cell` and render the same by default.
- Walkability checks: use `isinstance(x, Cell)` instead of checking subclasses.
- Partition smoothing: `Map.cellify_partitions()` opens partitions as `Corridor`
  tiles; keep docstrings brief.
- Color: default colorized output treats floors/corridors with the same grey
  (`boring_color`). Avoid per-type hues unless explicitly requested.

## Testing Guidelines
- Framework: `pytest` (see `pytest.ini` for `-v --ff --show-capture=stderr
  --maxfail=1`).
- Tests live in `t/`; name files `test_*.py`. Use `-k name` for focused runs.
- Keep tests deterministic; avoid network; isolate I/O (tmp paths/fixtures).
- Run `make test` before commits. Prefer small, verifiable changes; avoid
  unrelated fixes in the same patch.
- consider the availbe fixtures in t/confest.py -- if you need a map or player
  objects, the t/troom.py objects are the `objs` fixture and the troom itself is
  the `a_map` fixture.

### Test Style
- Prefer assertive code over comments; keep tests self-explanatory.
- When asserting exceptions, use `pytest.raises(..., match=regex)` to check
  the error message, not just the type.
- For parse failures, assert `not pstate`, `pstate.winner is None`, and check
  any available `pstate.error` text when relevant.

### Tests (Reminders)
- Do not attempt to import fixtures if they're already existing in t/conftest.py; just rely on the pytest fixture system
- Do not attempt to build new objects (livings, something to pick up, etc), use the `objs` fixture that's already loaded
- Do not attempt to load or initalize a map. the troom map is already available as the `a_map` fixture and already has the varous `objs` loaded into it
- Do not attempt to make new fixtures if you can get by with one that already exists

### Test Naming
- Use concise, descriptive function names that encode input and outcome.
- Positive parse cases: `test_open_door`, `test_open_south_door`.
- Negative parse cases end with `_fail`/`_fails`:
  `test_open_north_door_fail`, `test_open_nonsense_fails`.
- Multi-step flows describe the sequence succinctly:
  `test_open_door_and_move_through_it`.

## Commit & Pull Request Guidelines
- Commits: imperative subject line (<=72 chars); explain rationale when
  non-trivial.
- Keep diffs focused; reference issues (e.g., `Fixes #123`).
- PRs: include summary, motivation, test coverage, and any UX/build notes or
  screenshots.
- CI must pass: tests (`make test`) and hooks (`pre-commit`).

## Notes on Versioning & Build
- Version is generated by `setuptools_scm` into `space/version.py` (see
  `pyproject.toml`).
- Do not edit `space/version.py` manually; tag releases via Git to bump version
  metadata.
- For local development, do not install the package; run tests directly via
  `make test`.

## Agent Tips
- Be concise. Add minimal docstrings that explain purpose and key args; avoid
  long narratives.
- When adding flags like `cellify_partitions=True`, document with a very short
  phrase (e.g., "open short partitions").
- Prefer surgical changes; don’t refactor broadly unless asked.
- Respect `pytest.ini` settings; use `rg` for repo scans; read files in
  ≤250-line chunks.
- Only add code comments when they materially improve clarity. Avoid
  redundant or obvious comments; keep necessary comments short and direct.
 - Do not add conversational or meta comments in code. Comments must be about
   the code itself, not about prior discussion or rationale external to the
   codebase.
- Logging: do not configure global logging in scripts or modules. Use the
  project pattern: `import logging` and `log = logging.getLogger(__name__)`,
  then emit `log.debug/info/warning/error/exception` as needed. Global
  formatting/handlers are configured elsewhere.
- We favor TDD: add a failing test first, then implement the minimal
  code to make it pass. Keep tests focused, deterministic, and aligned with
  the current map/verb conventions.

### Parser/Router Respect
- Treat `space/router.py` and `space/parser.py` as core, high‑risk modules.
- Do not modify these files unless explicitly requested for that task.
- When a failure appears to originate from parsing/routing, first look for
  simpler explanations (e.g., parameter naming mismatches between `can_*`
  and `do_*` methods, or recent changes in verb implementations).
- Prefer minimal, surgical fixes in verb or actor classes (e.g., aligning
  `do_*` parameter names with keys returned by `can_*`) over changes to
  router/parser behavior.

Messaging
- When implementing or modifying verbs or behaviors that produce output,
  always read `MESSAGES.md` and follow its delivery/token rules.

### Robustness vs. Known Types
- When implementing verbs that operate on known engine types (e.g., `Living`),
  avoid defensive `getattr/hasattr` checks for attributes guaranteed by the
  type (e.g., `level`, `xp`, `hp`, `gender`, `height`, `weight`, `initiative`).
  If the parser allows invoking a verb on a player character, those attributes
  exist. Prefer direct attribute access to keep code clear and fail fast on
  actual programmer errors.
- STRONGER EMPHASIS: do not use getattr/hasattr without a very good reason.
  Provide justification and ask first. You're simply unable to understand when
  they should be used.

### Parser/Verb Tasks
- Before implementing or modifying verbs, skim `PARSER.md` for naming and
  routing conventions (e.g., `can_<verb>_obj` implies StdObj matching).
 - For command parsing or verb feature work, check `PARSER.md` first. It
   documents the `can_*`/`do_*` contract: the dict returned by `can_*` is
   forwarded as keyword args to `do_*`, so its keys must match the `do_*`
   parameter names.
- Prefer using the shell for compound commands in tests (e.g.,
  `me.do('open door; sSW6s3w')`).
- Do not change router hint logic in `space/args.py` to fit a single verb.
  Instead, follow the parameter naming conventions described in `PARSER.md`.

## Maintainer Preferences (Session Learnings)

- Small, clear fixes: proceed without asking; validate with focused tests.
  - Bias toward the smallest, test-local explanation first, but keep TDD in
    mind. Use these signals to decide whether to adjust tests or code:
    - If adjacent tests exercising the same subsystem are green and the
      failing case differs only in its expected string/parameterization,
      suspect a test expectation error first (inspect fixtures and ipython
      output before proposing code changes).
    - If writing a new feature/behavior (TDD), prefer adding a failing test
      and then changing code minimally to satisfy it. Do not contort parser/
      router/inform/compose to satisfy a single verb; align with
      PARSER.md/contract instead.
    - If multiple tests fail across modules after a change, suspect code.
      Revert to the smallest code fix that restores prior passing behavior
      while making the new test pass, or renegotiate the new test if it
      contradicts established behavior documented in PARSER.md or MESSAGES.md.
    - Always verify pronouns, names, token defaults, and fixtures (gender,
      locations, visibility) before assuming systemic messaging issues.
- Tests: prefer concise, targeted tests; avoid relying on complex fixtures
  when simpler environment-specific fixtures exist (e.g., use `e_map` over
  `a_map` for unobstructed movement).
- Assertions: use `assert ps` for `PState` truthiness; avoid tuple messages
  like `assert ps, ps.error`.
- Comments: DO NOT ADD COMMENTS without prior, explicit permission.
  - Ask only if something is genuinely unclear or cannot be expressed via
    clear naming or small helper functions.
  - If permission is granted, keep comments minimal and strictly about the
    code; no restating obvious logic, no narratives, no meta or conversational
    notes.
  - Prefer self-explanatory code (good names, tiny functions) over comments.

## Messaging System (Planning Notes)

- Source of inspiration: `contrib/lpc/m_messages.c` (LPC). Treat it as a reference
  for concepts only; port behavior into idiomatic Python within `space/`.
  Always re-scan `contrib/lpc/m_messages.c` when touching token defaults or
  composition semantics (e.g., `$t` defaults to index 1; `$o` defaults to 0).
  Cross-check `contrib/lpc/grammar.c`, `contrib/lpc/m_grammar.c`, and
  `contrib/lpc/names.c` for pronoun and naming behavior before changing
  `space/living/msg.py` or `space/named.py`.
- Placement: prefer a small `MessagesMixin` integrated into `Living`/`Humanoid`
  (likely on `Humanoid`) rather than a new global system. Keep surface area
  minimal and reuse existing shells and message types in `space/shell/`.
- Composition vs delivery: separate message composition (token expansion like
  `$N`, `$vverb`, `$t`, pronouns/possessives, and basic agreement) from
  delivery. Composition should return `TextMessage` instances; delivery should
  call `.tell()` on participants and nearby observers.
- Nearby delivery: fan‑out to “others” via the map/cell containers already in
  `space/map/cell/`. If a helper is required, add a minimal method on `Cell`
  to enumerate adjacent cells/occupants for audience collection. Avoid broad
  registries or globals.
- Grammar tokens: start with a practical subset: subjects `$N/$n`, target
  `$T/$t`, objects `$O/$o`, possessive/objective/reflexive `$p/$o/$r`, and
  verb agreement `$vverb`. Expand incrementally alongside tests.
- Gender/pronouns: follow the current `Living` gender model. Do not add
  defensive checks for attributes guaranteed by `Living` (e.g., `gender`,
  pronoun accessors once defined). Prefer direct attribute access.
- Shell integration: reuse `space/shell/message.TextMessage` and the existing
  `Living.tell()` plumbing (`HasShell.shell.receive`). Avoid introducing new
  sinks; format once, then deliver.
- Minimal environment changes: only add what’s needed to enumerate nearby
  `MessagesMixin` receivers. Floors and corridors should remain visually the
  same; any helper should be short and generic.
- Tests first: add focused tests in `t/` covering token expansion, agreement,
  self/target/others variants, and adjacency fan‑out. Keep tests deterministic
  and avoid router changes.
- Keep Pythonic: small pure functions for token parsing/expansion; avoid hidden
  globals. Any defaults/templates live on the mixin/class, not modules.

## Pattern Fidelity (Strong Emphasis)

- When implementing fixes or features that touch messaging, parsing, verbs, or
  tokens, you must follow established patterns in three places:
  - `t/` tests: extend existing tests in-place using their current structure
    and parametrization style instead of creating parallel or one-off tests.
  - `space/` Python code: mirror the module’s current helpers, regexes, and
    capitalization/qualifier handling. Prefer shims that integrate with
    existing functions over introducing new entry points.
  - `contrib/lpc/` reference: treat it as the behavioral model. Port semantics
    into idiomatic Python while keeping token names, defaults, and subject/
    target indexing consistent unless there is a documented divergence.

- Do not introduce new testing styles, helper functions, or token shapes when a
  matching pattern already exists. Extend parametrized cases rather than adding
  new test functions for near-identical coverage.

- For token work specifically:
  - Reuse the current regex tokenization shapes; add minimal deltas (e.g.,
    including a new leading tag) instead of wholesale rewrites.
  - Route behavior through existing helpers (e.g., `_name_for`, `_agree`) so
    capitalization, perspective, and defaults stay uniform.

- Any intentional divergence from `contrib/lpc` must be small, justified, and
  captured in tests first. Prefer pronoun-based simplifications over adding
  state unless tests require the more complex behavior.

## Git Usage Policy

- Using `git diff` and `git log` for context is encouraged.
- Do not run `git commit`, `git add`, or `git reset` from the agent under any circumstances.
- Do not use `git mv`. Just move files with `mv`; I will manage the repo myself
- in general, you're welcome to use git to gain insight into the code, but you
  may only do so in a read only fashion

## Python Version & Style Notes

- Target runtime: Python 3.8+ semantics, but avoid modern annotation syntax in
  function signatures (no `def fn(...) -> T` or union `A | B`).
- Prefer classic style definitions without return‑type annotations. Use docstrings
  or comments for type hints where helpful.
