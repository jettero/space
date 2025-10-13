"""
Generate emote verbs from the MudOS soul data.

This module exposes a lightweight `EmoteVerb` subclass and a `REGISTRY`
mapping verb name -> EmoteVerb instance generated from
`space.verb.emote.soul.SOUL`.

Parser/router wiring is intentionally deferred. We keep the verbs ready for
later integration where the router can ask the verb itself for can_/do_ logic.
"""

from space.verb.emote.soul import SOUL
from space.verb.base import Verb
from space.living.base import Living


class EmoteVerb(Verb):
    """Minimal emote verb container.

    - `name`: verb string (e.g., "smile").
    - `patterns`: mapping of signature tags to template(s), e.g.:
        "": "$N $vsmile.",
        "LIV": "$N $vsmile at $t.",
        "STR": "$N $vsmile $o.",
        "LIV STR": "$N $vsmile at $t $o."

    The `can_*`/`do_*` hooks are intentionally local to the verb so we don't
    need to modify `Living` yet. They are stubs for now; parser integration
    will call into these later.
    """

    def __init__(self, name, patterns):
        self.name = name
        self.patterns = patterns
        super().__init__()
        self._generate_methods()

    def _generate_methods(self):
        name = self.name
        for sig, template in self.patterns.items():
            sig = (sig or "").strip()
            if sig == "":
                self._add_noarg(name, template)
            elif sig == "LIV":
                self._add_liv(name, template)
            elif sig == "STR":
                self._add_str(name, template)
            elif sig == "WRD":
                self._add_wrd(name, template)
            elif sig == "OBJ":
                self._add_obj(name, template)
            elif sig == "LIV STR" or sig == "LIV  STR":
                self._add_liv_str(name, template)
            elif sig == "LIV LIV":
                self._add_liv_liv(name, template)
            elif sig == "LIV OBJ":
                self._add_liv_obj(name, template)
            # Ignore other rare forms for now; add as needed.

    # Each can_* returns kwargs matching do_* parameters, following PARSER.md
    def _add_noarg(self, name, template):
        def can_fn(actor):
            return True, {}

        def do_fn(actor):
            actor.simple_action(template)

        # Attach to Living so router can find them without changes
        setattr(Living, f"can_{name}", can_fn)
        setattr(Living, f"do_{name}", do_fn)

    def _add_liv(self, name, template):
        def can_fn(actor, living):
            return True, {"living": living}

        def do_fn(actor, living):
            actor.simple_action(template, living)

        setattr(Living, f"can_{name}_living", can_fn)
        setattr(Living, f"do_{name}_living", do_fn)

    def _add_str(self, name, template):
        def can_fn(actor, str_):
            return True, {"str_": str_}

        def do_fn(actor, str_):
            actor.simple_action(template, str_)

        setattr(Living, f"can_{name}", can_fn)
        setattr(Living, f"do_{name}", do_fn)

    def _add_wrd(self, name, template):
        def can_fn(actor, wrd):
            return True, {"wrd": wrd}

        def do_fn(actor, wrd):
            actor.simple_action(template, wrd)

        setattr(Living, f"can_{name}", can_fn)
        setattr(Living, f"do_{name}", do_fn)

    def _add_obj(self, name, template):
        def can_fn(actor, obj):
            return True, {"obj": obj}

        def do_fn(actor, obj):
            actor.simple_action(template, obj)

        setattr(Living, f"can_{name}_object", can_fn)
        setattr(Living, f"do_{name}_object", do_fn)

    def _add_liv_str(self, name, template):
        def can_fn(actor, living, str_):
            return True, {"living": living, "str_": str_}

        def do_fn(actor, living, str_):
            actor.simple_action(template, living, str_)

        setattr(Living, f"can_{name}_living", can_fn)
        setattr(Living, f"do_{name}_living", do_fn)

    def _add_liv_liv(self, name, template):
        def can_fn(actor, living, living2):
            return True, {"living": living, "living2": living2}

        def do_fn(actor, living, living2):
            actor.simple_action(template, living, living2)

        setattr(Living, f"can_{name}_living_living", can_fn)
        setattr(Living, f"do_{name}_living_living", do_fn)

    def _add_liv_obj(self, name, template):
        def can_fn(actor, living, obj):
            return True, {"living": living, "obj": obj}

        def do_fn(actor, living, obj):
            actor.simple_action(template, living, obj)

        setattr(Living, f"can_{name}_living_object", can_fn)
        setattr(Living, f"do_{name}_living_object", do_fn)


REGISTRY = list()


def load_emotes():
    """Build a registry of EmoteVerb objects from `SOUL` data."""
    global REGISTRY
    for name, patterns in SOUL["emotes"].items():
        REGISTRY.append(EmoteVerb(name=name, patterns=patterns))


load_emotes()
del load_emotes
