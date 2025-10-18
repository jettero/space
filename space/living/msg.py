# coding: utf-8

import re
from collections import namedtuple
from space.find import lazy_find_verb_method
import space.exceptions as E
from ..stdobj import StdObj

Messages = namedtuple("Messages", ["us", "them", "other"])
Actors = namedtuple("Actors", ["actor", "target"])


def capitalize(s):
    return s[:1].upper() + s[1:]


class Talks:
    def can_say_words(self, *words):
        return True, {"words": " ".join(words)}

    do_say_words = lazy_find_verb_method("say", "do_say_words")


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


class ReceivesMessages(HasShell, Talks):

    def select_pronoun(self, forwhom, subj, mode): # XXX renmove this
        if mode == "o":  # objective
            if subj is forwhom:
                return "you"
            return subj.objective
        if mode == "r":  # reflexive
            if subj is forwhom:
                return "yourself"
            return subj.reflexive
        if mode == "p":  # possessive
            if subj is forwhom:
                return "your"
            return subj.possessive
        if subj is forwhom:
            return "you"
        return subj.subjective

    def compose(self, forwhom, msg, who, *obs):
        def sub_token(m):
            t = m.group(0)
            if t.startswith("$v"):
                verb = t[2:]
                subj = who[0] if who else None
                if forwhom_is_subject:
                    return verb
                if verb == "are":
                    return "is"
                if verb == "have":
                    return "has"
                if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
                    return verb + "es"
                return verb + "s"
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
            # Top-level possessive/reflexive aliases:
            # $p/$P == $n0p/$N0p (subject's possessive)
            # $r/$R == $n0r/$N0r (subject's reflexive)
            if tag in ("p", "P", "r", "R"):
                if idx is None:
                    idx = 0
                if idx >= len(who) or not isinstance(who[idx], ReceivesMessages):
                    # Fallbacks: possessive -> "someone's" is awkward; keep "someone"
                    # reflexive -> "themself" is also awkward; use "themself" only when we have a subject
                    name = "someone"
                else:
                    subj = who[idx]
                    mode = "p" if tag in ("p", "P") else "r"
                    name = self.select_pronoun(forwhom, subj, mode)
                if tag in ("P", "R"):
                    return capitalize(name)
                return name
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
                    name = self.select_pronoun(forwhom, subj, qual)
                elif qual == "a":
                    name = subj.a_short
                else:
                    # Defaults: $n/$N -> subject; $t/$T -> a_short (use article),
                    # matching tests that expect indefinite for non-unique mobs.
                    if tag in ("T", "t"):
                        # If the recipient is the target, use objective pronoun "you"
                        if subj is forwhom:
                            name = self.select_pronoun(forwhom, subj, "o")
                        else:
                            name = subj.a_short
                    else:
                        # For $N/$n default to subject perspective ("you" when recipient is subject)
                        name = self.select_pronoun(forwhom, subj, "s")
                # Capitalize for upper-case tokens ($N/$T) when possible.
                if tag in ("N", "T"):
                    # For $N, when referring to a person and not the recipient, prefer short name capitalized
                    if tag == "N" and subj is not forwhom and qual not in ("o", "r", "p"):
                        return capitalize(subj.short)
                    return capitalize(name)
                # Lower-case for $n/$t; but keep exact if it already starts uppercase (proper name)
                return name if (name and name[0].isupper()) else name.lower()
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
                        return obj.the_short if tag == "o" else capitalize(obj.the_short)
                    if qual == "s":
                        return obj.short if tag == "o" else capitalize(obj.short)
                    # default and 'a'
                    return obj.a_short if tag == "o" else capitalize(obj.a_short)
                return str(obj) if tag == "o" else capitalize(str(obj))
            return t

        return re.sub(r"\$[MNVTTPPOOnnvttoPpRr][a-z0-9]*", sub_token, msg)

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
            for targ in src.location.map.visicalc_submap(src).objects:
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
        """Receive text from the mob shell
        Calling this on a player controlled living does nothing.
        Living objects with behaviors (aka mobs) will receive environment information via do_receive.
        Messages won't be delivered until it's the mob's turn and which point the mob will receive the nonsense message:
          `:EOF:YOUR_TURN:` and the your_turn flag (to this function) will be set to true.
        """
        # super().do_receive(msg, your_turn=your_turn)
        # raise NotImplementedError()
