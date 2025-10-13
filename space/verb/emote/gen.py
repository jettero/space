"""
Generate emote verbs from the MudOS soul data.

Parser/router wiring is intentionally deferred. We keep the verbs ready for
later integration where the router can ask the verb itself for can_/do_ logic.
"""

from space.verb.emote.soul import SOUL
from space.verb.base import Verb
from space.living.base import Living
from space.stdobj import StdObj


class Emote(Verb):
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
        def can_fn(actor, LIV: Living):
            return True, {"LIV": LIV}

        def do_fn(actor, LIV: Living):
            actor.simple_action(template, LIV)

        setattr(Living, f"can_{name}_LIV", can_fn)
        setattr(Living, f"do_{name}_LIV", do_fn)

    def _add_str(self, name, template):
        def can_fn(actor, STR):
            return True, {"STR": STR}

        def do_fn(actor, STR):
            actor.simple_action(template, STR)

        setattr(Living, f"can_{name}", can_fn)
        setattr(Living, f"do_{name}", do_fn)

    def _add_wrd(self, name, template):
        def can_fn(actor, WRD):
            return True, {"WRD": WRD}

        def do_fn(actor, WRD):
            actor.simple_action(template, WRD)

        setattr(Living, f"can_{name}", can_fn)
        setattr(Living, f"do_{name}", do_fn)

    def _add_obj(self, name, template):
        def can_fn(actor, OBJ: StdObj):
            return True, {"OBJ": OBJ}

        def do_fn(actor, OBJ: StdObj):
            actor.simple_action(template, OBJ)

        setattr(Living, f"can_{name}_OBJ", can_fn)
        setattr(Living, f"do_{name}_OBJ", do_fn)

    def _add_liv_str(self, name, template):
        def can_fn(actor, LIV: Living, STR):
            return True, {"LIV": LIV, "STR": STR}

        def do_fn(actor, LIV: Living, STR):
            actor.simple_action(template, LIV, STR)

        setattr(Living, f"can_{name}_LIV", can_fn)
        setattr(Living, f"do_{name}_LIV", do_fn)

    def _add_liv_liv(self, name, template):
        def can_fn(actor, LIV: Living, LIV2: Living):
            return True, {"LIV": LIV, "LIV2": LIV2}

        def do_fn(actor, LIV: Living, LIV2: Living):
            actor.simple_action(template, LIV, LIV2)

        setattr(Living, f"can_{name}_LIV_LIV", can_fn)
        setattr(Living, f"do_{name}_LIV_LIV", do_fn)

    def _add_liv_obj(self, name, template):
        def can_fn(actor, LIV: Living, OBJ: StdObj):
            return True, {"LIV": LIV, "OBJ": OBJ}

        def do_fn(actor, LIV: Living, OBJ: StdObj):
            actor.simple_action(template, LIV, OBJ)

        setattr(Living, f"can_{name}_LIV_OBJ", can_fn)
        setattr(Living, f"do_{name}_LIV_OBJ", do_fn)


def load_emotes():
    ret = list()
    for name, patterns in SOUL["emotes"].items():
        ret.append(Emote(name=name, patterns=patterns))
    return ret


REGISTRY = load_emotes()
del load_emotes
