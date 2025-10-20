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

    @classmethod
    def _parse_sig(cls, raw):
        if not raw:
            return []
        parts = []
        for tok in raw.replace("  ", " ").strip().split(" "):
            if tok.isupper():
                parts.append(tok)
            elif tok:
                parts.append(("WRD", tok))
        return parts

    @classmethod
    def _arg_names(cls, parts):
        res = []
        counts = {}
        for p in parts:
            if isinstance(p, tuple):
                base = "WRD"
            else:
                base = p
            n = counts.get(base, 0)
            counts[base] = n + 1
            res.append(base if n == 0 else f"{base}{n}")
        return res

    @classmethod
    def _type_for(cls, p):
        if p == "LIV":
            return ": Living"
        if p == "OBJ":
            return ": StdObj"
        return ""

    @classmethod
    def _safe_name(cls, name):
        return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in name)

    @classmethod
    def _sig_key(cls, name, parts):
        def s(x):
            return x if isinstance(x, str) else x[0]

        return name + "::" + " ".join(s(p) for p in parts)

    @classmethod
    def _make_call_fn(cls, name, parts):
        key = cls._sig_key(name, parts)
        arg_names = cls._arg_names(parts)
        core = []
        for p in parts:
            if isinstance(p, str):
                core.append(p)
            else:
                core.append(p[1] if p[1].isalpha() else p[0])
        if core == ["WRD"] and any(isinstance(p, tuple) for p in parts):
            pass
        elif core == ["WRD"]:
            core = ["STR"]
        params = []
        ai = iter(arg_names)
        for p in parts:
            if isinstance(p, tuple):
                params.append(next(ai))
            else:
                a = next(ai)
                params.append(f"{a}{cls._type_for(p)}")
        can_name = "can_" + name + ("_" + "_".join(core) if core else "")
        safe_def = cls._safe_name(can_name)
        body_k = ", ".join([f'"{a}": {a}' for a in arg_names])
        checks = []
        ai = iter(arg_names)
        for p in parts:
            if isinstance(p, tuple):
                an = next(ai)
                checks.append(f"({an} == '{p[1]}')")
            elif p in ("LIV", "OBJ", "STR", "WRD"):
                next(ai, None)
        guard = (" and ".join(checks)) or "True"
        src = f"def {safe_def}(self{(', ' + ', '.join(params)) if params else ''}):\n    return ({guard}) and bool({len(parts)}) and any(True for _ in ((),)), {{{body_k}}}\n"
        ns = {"Living": Living, "StdObj": StdObj}
        exec(src, ns)
        fn = ns[safe_def]
        fn.__name__ = can_name
        return fn

    @classmethod
    def _make_do_fn(cls, name, parts, template):
        key = cls._sig_key(name, parts)
        arg_names = cls._arg_names(parts)
        core = []
        for p in parts:
            if isinstance(p, str):
                core.append(p)
            else:
                core.append(p[1] if p[1].isalpha() else p[0])
        if core == ["WRD"] and any(isinstance(p, tuple) for p in parts):
            pass
        elif core == ["WRD"]:
            core = ["STR"]
        params = []
        ai = iter(arg_names)
        for p in parts:
            if isinstance(p, tuple):
                params.append(next(ai))
            else:
                a = next(ai)
                params.append(f"{a}{cls._type_for(p)}")
        do_name = "do_" + name + ("_" + "_".join(core) if core else "")
        safe_def = cls._safe_name(do_name)
        args = ", ".join(arg_names)
        src = f"def {safe_def}(self{(', ' + ', '.join(params)) if params else ''}):\n    self.simple_action(template{(', ' + args) if args else ''})\n"
        ns = {"Living": Living, "StdObj": StdObj, "template": template}
        exec(src, ns)
        fn = ns[safe_def]
        fn.__name__ = do_name
        return fn

    def _generate_methods(self):
        name = self.name
        for raw_sig, template in self.patterns.items():
            parts = self._parse_sig(raw_sig)
            can_fn = self._make_call_fn(name, parts)
            do_fn = self._make_do_fn(name, parts, template)
            setattr(Living, can_fn.__name__, can_fn)
            setattr(Living, do_fn.__name__, do_fn)


def load_emotes():
    return list(Emote(name=name, patterns=patterns) for name, patterns in SOUL["emotes"].items())
