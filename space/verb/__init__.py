# coding: utf-8

from ..find import find_by_classname


def find_verbs():
    return find_by_classname("space.verb", "Action")


def load_verbs():
    from .emote.gen import REGISTRY

    return [c() for c in find_verbs()] + REGISTRY
