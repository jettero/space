Constructing Verbs

- Goal: focus on building verbs and how they interact with actors (Livings).
  Parser internals and scoring live near the code in `space/parser.py` as
developer notes.

Core Pieces for Verbs
- Base class: `space/verb/base.py: Verb`
- Implementations: `space/verb/<name>.py` exposing `Action(Verb)`
- Actor methods: `can_<verb>_*` and `do_<verb>_*` on the acting object (often
  `space/living/base.py: Living`)

 Verbs
- `name`: canonical verb name (defaults to module name; e.g., `attack`).
- `nick`: optional list of aliases; prefix matches are accepted (e.g., `att` →
  `attack`). You do not need to specify `nick = ['look']` (or similar) when the
  verb has no extra aliases — the canonical `name` is always recognized. If you
  do provide `nick`, include `name` only when you also add actual aliases.
- `preprocess_tokens(me, **tokens)`: normalize token dict before routing.
  Example: `move.Action` converts direction strings like `"2sse"` into a
  tuple `("s","s","s","e")` under the `moves` key.
- Helpers: `Verb.can()` and `Verb.do()` delegate to the actor’s
  `parse_can/parse_do`.
- Discovery: each module under `space/verb/` exports an `Action(Verb)` class;
  `space/verb/__init__.py:load_verbs()` instantiates them and the parser picks
  among them by `name`/`nick`.

Actor Side (Living)
- Implement capability methods on the actor that will execute the verb.
- Pattern: `can_<verb>_<specifics>(...) -> (bool, dict)` and
  `do_<verb>_<specifics>(...) -> None`.
  - The `can_...` method validates and may enrich arguments (e.g., resolve
    targets). Return `(False, {"error": "message"})` to produce a user error.
  - The `do_...` method performs the action with validated args.
- Naming controls routing specificity: longer suffixes win. For example,
  `can_move_obj_words` is chosen over `can_move_words` when both fit.
- Examples in `space/living/base.py`:
  - Movement: `can_move_words`, `do_move_words`, and `can_move_obj_words`.
  - Attack: `can_attack_living`, `do_attack`.
  - Look: `can_look`, `do_look`.

Hints and Argument Resolution
- The system derives argument expectations for your `can_...` methods:
  - Use annotations to specify types or predicates (e.g., `target: Living`).
  - Without annotations, names drive inference: `obj*` → `Containable`,
    `living*`/`target*` → `Living`, otherwise `str`.
- For multi-word/free-form tails, accept a varargs parameter (e.g., `*moves`)
  which the verb’s `preprocess_tokens` can convert (see `move`).
- Matching by name/id leverages `baseobj.parse_match` (tokens from `short`,
  `long`, class name, and `abbr`).

Execution Path (Brief)
- Parser picks the verb by `name`/`nick`, collects hints from `can_...`
  methods, fills tokens to arguments, then calls the best `do_...`.
  Implementation details and scoring are documented inline in
  `space/parser.py` for maintainers.

Object Matching
- `baseobj.parse_match(txt, id_=None)` matches by id prefix/suffix or by token
  prefix. Single‑character abbreviations are case‑sensitive.

Execution
- `Parser.parse(me, text)` returns a `PState`. Calling it runs the selected
  `do_<verb>` on the actor with validated arguments, or raises `E.ParseError` on
  failure.

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

Concrete Construction Examples

Attack
```
# space/verb/attack.py
from .base import Verb

class Action(Verb):
    name = 'attack'
    nick = 'attack kill hit'.split()

# actor side (e.g., on Living)
def can_attack_living(self, living):
    # resolve a valid nearby target from a list of Living matches
    # return (True, { 'target': best }) or (False, { 'error': '...' })
    ...

def do_attack(self, target):
    # perform the attack
    ...
```

Look
```
# space/verb/look.py
from .base import Verb

class Action(Verb):
    name = 'look'

# actor side (e.g., on Living)
def can_look(self):
    return True, {}

def do_look(self):
    # render surroundings / map
    ...
```

Note: The built-in "move" verb uses shortcut direction parsing and is not a
great minimal example, so it is omitted here.

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
