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

    def compose(self, forwhom, msg, who, *obs):
        def sub_token(m):
            t = m.group(0)

            if t.startswith("$v"):
                verb = t[2:]
                if who and who[0] == forwhom:
                    return verb
                if verb == "are":
                    return "is"
                if verb == "have":
                    return "has"
                if verb.endswith(("s", "sh", "ch", "x", "z", "o")):
                    return verb + "es"
                return verb + "s"

            cap = t[1].isupper()
            tag = t[1].lower()
            rest = t[2:]

            if rest and rest[0].isdigit():
                idx = int(rest[0])
                qual = rest[1:]
            else:
                idx = 1 if tag == "t" else 0
                qual = rest

            if tag in "prtn" and not (idx < len(who) and isinstance(who[idx], ReceivesMessages)):
                if tag == "p":
                    return "Someone's" if cap else "someone's"
                if tag == "r":
                    return "Itself" if cap else "itself"
                if tag in ("t", "n"):
                    return "Someone" if cap else "someone"
            elif tag == "o" and idx >= len(obs):
                return "Something" if cap else "something"

            if tag == "p":
                name = "your" if who == forwhom else who[idx].possessive
                return capitalize(name) if cap else name

            if tag == "r":
                name = "yourself" if who[idx] == forwhom else who[idx].reflexive
                return capitalize(name) if cap else name

            if tag == "n":
                if qual == "o":
                    name = "you" if who[idx] == forwhom else who[idx].objective
                elif qual == "r":
                    name = "yourself" if who[idx] == forwhom else who[idx].reflexive
                elif qual == "p":
                    name = "your" if who[idx] == forwhom else who[idx].possessive
                elif qual == "a":
                    name = who[idx].a_short
                else:
                    name = "you" if who[idx] == forwhom else who[idx].subjective
                return capitalize(name) if cap else name

            if tag == "t":
                if qual == "o":
                    name = "you" if who[idx] == forwhom else who[idx].objective
                elif qual == "r":
                    name = "yourself" if who[idx] == forwhom else who[idx].reflexive
                elif qual == "p":
                    name = "your" if who[idx] == forwhom else who[idx].possessive
                elif qual == "a":
                    name = who[idx].a_short
                else:
                    name = "you" if who[idx] == forwhom else who[idx].a_short
                return capitalize(name) if cap else name

            if tag == "o":
                if isinstance(obs[idx], StdObj):
                    if qual == "t":
                        name = obs[idx].the_short
                    elif qual == "s":
                        name = obs[idx].short
                    else:
                        name = obs[idx].a_short
                else:
                    name = str(obs[idx])
                return capitalize(name) if cap else name
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
