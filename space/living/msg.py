# coding: utf-8

import re
from ..stdobj import StdObj

class HasShell:
    _shell = None

    @property
    def shell(self):
        if self._shell is None:
            from ..shell.log import Shell as LogShell

            self._shell = LogShell(owner=self)
        return self._shell

    @shell.setter
    def shell(self, v):
        from ..shell.base import BaseShell

        if v is None:
            self._shell = v
        if not isinstance(v, BaseShell):
            raise E.STypeError(f"{v} is not a shell")
        self._shell = v

    def tell(self, msg):
        self.shell.receive(msg)



class ReceivesMessages(HasShell):
    def _a_an(self, word):
        w = str(word)
        return ("an " + w) if (w[:1].lower() in "aeiou") else ("a " + w)

    def _short(self, x, the=False, a=False):
        if isinstance(x, StdObj):
            s = x.short
        else:
            s = str(x)
        if the:
            return f"the {s}"
        if a:
            return self._a_an(s)
        return s

    def _name_for(self, forwhom, subj, mode):
        if mode == "o":  # objective
            if subj is forwhom:
                return "you"
            return getattr(subj, "objective", "them")
        if mode == "r":  # reflexive
            if subj is forwhom:
                return "yourself"
            return getattr(subj, "reflexive", "themself")
        if mode == "p":  # possessive
            if subj is forwhom:
                return "your"
            return getattr(subj, "possessive", "their")
        # subject
        if subj is forwhom:
            return "You"
        return getattr(subj, "subjective", getattr(subj, "short", str(subj)))

    def _agree(self, forwhom_is_subject, verb):
        if forwhom_is_subject:
            return verb
        # naive third-person singular inflection
        if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
            return verb + "es"
        return verb + "s"

    def _expand(self, forwhom, msg, who, obs):
        def sub_token(m):
            t = m.group(0)
            if t.startswith("$v"):
                verb = t[2:]
                subj = who[0] if who else None
                return self._agree(forwhom is subj, verb)
            tag = t[1]
            rest = t[2:]
            idx = None
            qual = ""
            # optional index
            if rest and rest[0].isdigit():
                idx = int(rest[0])
                qual = rest[1:]
            else:
                qual = rest
            if tag in ("N", "n", "T", "t"):
                if tag in ("T", "t"):
                    if idx is None:
                        idx = 1
                else:
                    if idx is None:
                        idx = 0
                # require recipients to be message-capable, not specific class
                if idx >= len(who) or not isinstance(who[idx], ReceivesMessages):
                    return "someone"
                subj = who[idx]
                if qual in ("o", "r", "p"):
                    return self._name_for(forwhom, subj, qual)
                if qual == "a":
                    return self._short(subj, a=True)
                # default subject/short
                return self._name_for(forwhom, subj, "s")
            if tag in ("O", "o"):
                if idx is None:
                    idx = 1
                if idx >= len(obs):
                    return "something"
                obj = obs[idx]
                if qual == "t":
                    return self._short(obj, the=True)
                if qual == "a":
                    return self._short(obj, a=True)
                return self._short(obj)
            return t

        return re.sub(r"\$[MNVTTPPOOnnvtto][a-z0-9]*", sub_token, msg)

    def compose(self, forwhom, msg, who, *obs):
        return self._expand(forwhom, msg, who, list(obs))

    def action(self, who, msg, *obs):
        us = self.compose(who[0], msg, who, *obs)
        them = None
        if len(who) > 1:
            them = self.compose(who[1], msg, who, *obs)
        others = self.compose(None, msg, who, *obs)
        return us, them, others

    def inform(self, who, msgs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        actor = who[0]
        us, them, others = msgs
        seen = set()
        if us is not None:
            actor.tell(us)
            seen.add(actor)
        if them is not None and len(who) > 1 and who[1] is not None:
            targ = who[1]
            if targ not in seen:
                targ.tell(them)
                seen.add(targ)
        sub = actor.location.map.hearicalc_submap(actor, maxdist=range, min_hearability=min_hearability)
        for obj in getattr(sub, "objects", []):
            if isinstance(obj, ReceivesMessages) and obj not in seen and obj not in who:
                obj.tell(others)
                seen.add(obj)

    def simple_action(self, msg, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = [self]
        self.inform(who, self.action(who, msg, *obs), range=range, min_hearability=min_hearability)

    def my_action(self, msg, *obs):
        who = [self]
        us, _, _ = self.action(who, msg, *obs)
        self.tell(us)

    def other_action(self, msg, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = [self]
        _, _, others = self.action(who, msg, *obs)
        self.inform(who, (None, None, others), range=range, min_hearability=min_hearability)

    def targeted_action(self, msg, target, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = [self, target]
        self.inform(who, self.action(who, msg, *obs), range=range, min_hearability=min_hearability)
