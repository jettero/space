#!/usr/bin/env python
# coding: utf-8

import os
from ..find import find_by_classname
from .base import Verb, VerbError


def find_action_classes():
    return find_by_classname("space.verb", "Action")


def load_verbs():
    if os.environ.get("SPACE_DISABLE_EMOTE_REGISTRY", False):
        return [c() for c in find_action_classes()]

    from .emote import EMOTES

    return [c() for c in find_action_classes()] + list(EMOTES.values())


VERBS = {v.name: v for v in load_verbs()}
VERBS.update({n: v for v in VERBS.values() for n in v.nick if n not in VERBS})


def find_verb(x):
    if x and isinstance(x, str):
        x = x.lower()
        if v := VERBS.get(x):  # exact matching via get()
            return {v}
        return {v for n, v in VERBS.items() if v.match(x)}
    return set()

def register_outside_verb(x):
    if not isinstance(x, Verb):
        raise TypeError(f"{x!r} is not an Verb instance")
    if x.name in VERBS and VERBS[x.name] is not x:
        raise VerbError(f"\"{x.name}\" is already a registered verb and it doesn't seem to be {x!r}")
    VERBS[x.name] = x
    for n in x.nick:
        if n not in VERBS:
            VERBS[n] = x
    
