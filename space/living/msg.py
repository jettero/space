# coding: utf-8

import re
from collections import namedtuple
import space.exceptions as E
from ..stdobj import StdObj

Messages = namedtuple("Messages", ["us", "them", "other"])
Actors = namedtuple("Actors", ["actor", "target"])


class HasShell:
    _shell = None

    @property
    def shell(self):
        if self._shell is None:
            from ..shell.log import Shell as LogShell

            self.shell = LogShell()
        return self._shell

    @shell.setter
    def shell(self, v):
        from ..shell.base import BaseShell

        if v is None:
            self._shell = v
        if not isinstance(v, BaseShell):
            raise E.STypeError(f"{v} is not a shell")
        if self._shell is not v:
            self._shell = v
            v.owner = self

    def tell(self, msg):
        self.shell.receive(msg)


class ReceivesMessages(HasShell):

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
        # We only handle verbs written in second-person present.
        # If the subject is the addressee, keep the verb as-is (e.g., "you attack").
        if forwhom_is_subject:
            return verb
        # Third-person present for others. Handle "be" specially and otherwise
        # inflect with simple -s/-es rules from the 2nd-person form.
        if verb == "are":
            return "is"
        if verb == "have":
            return "has"
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
                    return subj.a_short
                # default subject/short
                return self._name_for(forwhom, subj, "s")
            if tag in ("O", "o"):
                # Objects default to first observed ($o0), not second
                if idx is None:
                    idx = 0
                if idx >= len(obs):
                    return "something"
                obj = obs[idx]
                # Qualifiers: default -> a_short, 's' -> short, 't' -> the_short, 'a' -> a_short
                if isinstance(obj, StdObj):
                    if qual == "t":
                        return obj.the_short
                    if qual == "s":
                        return obj.short
                    # default and 'a'
                    return obj.a_short
                # Non-StdObj fallback (strings)
                if qual == "t":
                    return f"the {obj}"
                if qual == "s":
                    return str(obj)
                # default/a
                w = str(obj)
                return (f"an {w}") if w[:1].lower() in "aeiou" else (f"a {w}")
            return t

        return re.sub(r"\$[MNVTTPPOOnnvtto][a-z0-9]*", sub_token, msg)

    def compose(self, forwhom, msg, who, *obs):
        return self._expand(forwhom, msg, who, obs)

    def action(self, who: Actors, msg, *obs):
        us = self.compose(who.actor, msg, who, *obs)
        them = self.compose(who.target, msg, who, *obs) if who.target is not None else None
        others = self.compose(None, msg, who, *obs)
        return Messages(us, them, others)

    def inform(self, who: Actors, msgs: Messages, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        seen = set()
        if msgs.us is not None:
            who.actor.tell(msgs.us)
            seen.add(who.actor)
        if msgs.them is not None and who.target is not None and who.target not in seen:
            who.target.tell(msgs.them)
            seen.add(who.target)
        for src in who:
            if src is None:
                continue
            for targ in src.location.map.visicalc_submap(src, maxdist=range).objects:
                if isinstance(targ, ReceivesMessages) and targ not in seen:
                    targ.tell(msgs.other)
                    seen.add(targ)

    def simple_action(self, msg, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = Actors(self, None)
        self.inform(who, self.action(who, msg, *obs), range=range, min_hearability=min_hearability)

    def my_action(self, msg, *obs):
        who = Actors(self, None)
        us, _, _ = self.action(who, msg, *obs)
        self.tell(us)

    def other_action(self, msg, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = Actors(self, None)
        _, _, others = self.action(who, msg, *obs)
        self.inform(who, Messages(None, None, others), range=range, min_hearability=min_hearability)

    def targeted_action(self, msg, target, *obs, range=6, min_hearability=0.1):  # pylint: disable=redefined-builtin
        who = Actors(self, target)
        self.inform(who, self.action(who, msg, *obs), range=range, min_hearability=min_hearability)

    def do_receive(self, msg, your_turn=False):
        """ Receive text from the mob shell
            Calling this on a player controlled living does nothing.
            Living objects with behaviors (aka mobs) will receive environment information via do_receive.
            Messages won't be delivered until it's the mob's turn and which point the mob will receive the nonsense message:
              `:EOF:YOUR_TURN:` and the your_turn flag (to this function) will be set to true.
        """
        raise NotImplementedError()
