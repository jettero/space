# coding: utf-8

import os
from ..find import find_by_classname


def find_verbs():
    return find_by_classname("space.verb", "Action")


def load_verbs():
    if os.environ.get("SPACE_DISABLE_EMOTE_REGISTRY", False):
        return [c() for c in find_verbs()]

    from .emote.gen import REGISTRY
    return [c() for c in find_verbs()] + REGISTRY
