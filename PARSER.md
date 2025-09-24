Parser, Verbs, and Living Objects

- Goal: explain how free‑text input like "attack jaime" or "2sse" becomes a
  routed method call on the player (a Living object), with arguments resolved to
in‑world objects or directions.

Core Pieces
- Parser: `space/parser.py`
- Verbs: `space/verb/*` with base in `space/verb/base.py`
- Router: `space/router.py` and `space/args.py`
- Living objects: `space/living/*` (notably `space/living/base.py`)
- Object matching: `space/obj.py`

High‑Level Flow
- Input comes in as a string and is tokenized by `shlex.split`.
- The first token selects a verb (with fuzzy/prefix matching against each verb’s
  nicknames). If no verb matches and the input is a direction string (e.g.,
`2sse`), it is rewritten as `move <dirs>`.
- The parser builds a plan of possible method routes for the chosen verb on the
  acting Living (“me”), using the router to discover `can_<verb>` variants and
their argument hints.
- Tokens are preprocessed by the Verb (e.g., expand directions) and then filled
  into hinted arguments by scanning visible in‑map objects and applying
type/annotation rules.
- Each candidate route is evaluated by calling the `can_<verb>` method, which
  must return `(bool, kwargs)`. Truthy candidates become executable, with
accumulated `do_args`.
- The highest‑scoring candidate becomes the winner. Calling the PState then
  invokes `do_<verb>` with `do_args`.

Verbs
- Class: `space/verb/base.py: Verb`
  - `name`: canonical verb (defaults to module name; e.g., `attack`).
  - `nick`: list of recognized aliases/prefixes. `match()` accepts prefixes
    (`att` → `attack`).
  - `preprocess_tokens(me, **tokens)`: optional normalization step (e.g.,
    turning `"nsew"` into a tuple of moves). See `space/verb/move.py`.
  - `can()` / `do()`: convenience wrappers around the Living’s `parse_can` /
    `parse_do` machinery.
- Implementations live under `space/verb/` and expose an `Action` class
  (discovered by `space/verb/__init__.py:load_verbs`). Examples:
  - move: converts direction strings to canonical move tuples.
  - attack, look, open: basic verbs with names/aliases.

Living Objects and Capabilities
- Base: `space/living/base.py: Living`
  - Provides verb implementations via `can_<verb>` and `do_<verb>` methods.
  - Movement (`CanMove` mixin):
    - `can_move_words(self, *moves, obj:Containable=None)` validates a path and
      returns `(True, {"moves": moves})` or `(False, {"error": ...})`.
    - `do_move_words(self, *moves)` executes the movement.
    - Object‑move variants (e.g., `can_move_obj_words`, `do_move_obj_words`)
      allow moving another contained object; the router chooses the longest
matching name.
  - Combat:
    - `can_attack_living(self, living)`: resolves nearest match within range and
      returns either `(True, {"target": <Living>})` or `(False, {"error":
...})`.
    - `do_attack(self, target)`: applies damage and sends messages.
  - Look:
    - `can_look(self)`: currently accepts any extra words; `do_look` renders the
      visible submap and a confirmation message.

Routing and Argument Inference
- Method discovery: `MethodArgsRouter` and `MethodNameRouter`
  (`space/router.py`).
  - `MethodArgsRouter(obj, "can_<verb>")`: yields `RouteHint`s for each matching
    method on the object. Hints include parameter names and expected types.
  - `MethodNameRouter(obj, "do_<verb>")`: chooses the most specific method name
    based on provided keyword segments (e.g., `do_move_obj_words` over
`do_move_words`).
- Hint generation: `space/args.py:introspect_hints(fn)`
  - Inspects parameters and annotations to build `IntroHint`s. Heuristics:
    - `*args` gets type `tuple`.
    - If annotated, use that type/predicate/regexp.
    - Otherwise infer by name: `obj*` → `Containable`, `living*`/`target*` →
      `Living`, else `str`.
- Token filling: `RouteHint.fill(objs)`
  - Uses the preprocessed token dict and the visible objects `pstate.objs` (from
    `me.location.map.visicalc_submap(me)`) to resolve types:
    - For object types, matches by `obj.parse_match()` (see below), returning
      lists for plural tokens or a single match as applicable.
    - For tuples/lists, preserves sequences.
- Safe execution: `space/args.py:safe_execute(fn, *a, **kw)`
  - Finds a compatible `(args, kwargs)` via `introspect_args` and calls the
    function. If insufficient, raises `UnfilledArgumentError` which the parser
treats as “not filled yet”.

Parsing State and Scoring
- `PState(me, text)`: holds tokens, verb candidates, visible objects, assembled
  `PSNode`s and final winner.
  - `PSNode`: one node per verb and per candidate `can_...` method; tracks
    filled args, evaluated status, and links to siblings/children.
  - Filling: `PState.plan()` attaches `RouteHint`s for each `can_<verb>` and
    stores preprocessed tokens on them. `PSNode.fill()` computes concrete
argument values from tokens and visible objects.
  - Evaluation: `PSNode.evaluate()` calls `can_...()`; sets `can_do` and merges
    additional kwargs into `do_args`.
  - Scoring: `PSNode.score`
    - 2.x for `can_do == True` (higher if more args present), 1 when all hinted
      args are filled but not yet permitted, else 0 with fractional propagation
across children to prefer deeper matches.
  - Winner: highest score across the node tree. `bool(PState)` is True only when
    there is a winner and it’s allowed (`can_do`).
  - Error: `PState.error` builds a user message either from the best candidate’s
    `error` kwarg or a generic “unable to understand”. Extra tokens that didn’t
fit cause planning to reject that hint, surfacing in error text (see tests).

Object Matching
- `space/obj.py: baseobj.parse_match(txt, id_=None)`
  - Accepts an id prefix/suffix match or token prefix match against the object’s
    token set:
    - Tokens come from `short`, `long`, class name, and `abbr`.
    - Single‑character abbreviations are case‑sensitive.

Execution
- `Parser.parse(me, text)` returns a `PState`.
- Calling the `PState` invokes the winning `do_<verb>` via `MethodArgsRouter`
  with `do_args`. The actor’s `active` flag is set for the duration (affects map
glyph).
- If there is no winning candidate or a `can_...` produced an error, invoking
  raises `E.ParseError` with the message from `PState.error`.

Examples
- Move by direction string:
  - Input: `"2sse"` → rewritten to `"move 2sse"` → `preprocess_tokens()` turns
    into `moves=('s','s','s','e')` → `can_move_words()` approves →
`do_move_words()` executes.
- Attack by name:
  - Input: `"attack jaime"` → `find_verb()` picks `attack` → hint infers
    `living` param → `RouteHint.fill()` picks nearest matching Living in range →
`can_attack_living()` returns `(True, {"target": <Living>})` →
`do_attack(target)` applies damage.

Adding New Verbs
- Create `space/verb/<name>.py` with an `Action(Verb)` subclass. Optionally
  override `nick` and `preprocess_tokens`.
- On the relevant actor class (often `Living`), implement one or more
  `can_<name>_*` and `do_<name>_*` methods. Keep names descriptive; the name
router prefers longer suffixes when multiple match (e.g., `_obj_words` vs
`_words`).
- For argument hints, use type annotations or parameter names to steer
  inference:
  - Annotate with classes (e.g., `target: Living`) or regex/predicate callables.
  - Or name parameters `obj*`, `living*`, `target*` to trigger default
    inference.

Notes and Guarantees
- `can_<verb>` methods must return `(bool, dict)`; the dict may include `error`
  for user‑facing failures.
- `do_<verb>` methods should assume arguments were validated and present.
- Tokens beyond what a hint expects cause that hint to be rejected; if no hint
  accepts the token shape, the best verb still wins for suggestions, but the
PState is falsey and will raise on call (see `t/test_parser.py`).
