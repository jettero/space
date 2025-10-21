"""
Generate emote verbs from the MudOS soul data.

Parser/router wiring is intentionally deferred. We keep the verbs ready for
later integration where the router can ask the verb itself for can_/do_ logic.
"""

import re
import logging
from space.verb.emote.soul import SOUL
from space.verb.base import Verb
from space.living.base import Living
from space.stdobj import StdObj

log = logging.getLogger(__name__)

BLESSED_TOKENS = {
    "LIV": ("liv", "{aname}:Living"),
    "OBJ": ("obj", "{aname}:StdObj"),
    "WRD": ("word", "{aname}:str"),
    "STR": ("words", "{aname}:tuple[str,...]"),
}

SAFE_TOKEN = re.compile(r"^[a-zA-Z][A-Za-z0-9-]+$")


class Emote(Verb):
    def __init__(self, name, patterns):
        if not SAFE_TOKEN.match(name):
            raise ValueError(f'"{name}" is not a good name for an emote')
        self.name = name
        for sig, template in patterns.items():
            self.generate_can_fn(sig, template)
            self.generate_do_fn(sig, template)
        super().__init__()

    def generate_can_fn(self, sig, template, on_cls=Living):
        tokens = [x for x in sig.split(" ") if x]
        fn_name = ["can", self.name.replace("-", "_")]
        fn_vars = list()
        specifics = dict()
        counts = dict()
        for token in tokens:
            try:
                aname, afmt = BLESSED_TOKENS[token]
            except KeyError:
                aname, afmt = BLESSED_TOKENS["WRD"]
                if not SAFE_TOKEN.match(token):
                    raise ValueError(f'"{token}" is not a good token for an emote syntax key')
                specifics[aname] = token
            fn_name.append(aname)
            try:
                aname = f"{aname}{counts[aname]}"
                counts[aname] += 1
            except KeyError:
                counts[aname] = 1

            fn_vars.append((aname, afmt.format(aname=aname)))

        fn_name = "_".join(fn_name)
        if hasattr(Living, fn_name):
            raise ValueError(f"Living.{fn_name} already exists")
        fn_args = [x for _, x in fn_vars]
        source_code = f'def {fn_name}({", ".join(["self", *fn_args])}):\n'
        for k, v in specifics.items():
            source_code += f'\tif {k} != "{v}":\n\t\treturn False, {{"error": f"unknown token: {{{k}}}"}}\n'
        source_code += "\treturn True, {"
        for aname, ahint in fn_vars:
            if ahint.startswith("*"):
                source_code += f'"{aname}": " ".join({aname}), '
            else:
                source_code += f'"{aname}": {aname}, '
        source_code += "}\n"
        log.debug("############### WTF\n\n%s\n\n############### WTF", source_code)
        setattr(on_cls, fn_name, exec(source_code))

    def generate_do_fn(self, sig, template, on_cls=Living):
        pass


EMOTES = None


def load_emotes():
    global EMOTES
    if not EMOTES:
        EMOTES = list(Emote(name=name, patterns=patterns) for name, patterns in SOUL["emotes"].items())
    return EMOTES
