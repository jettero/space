# coding: utf-8

from .base import Verb


class Action(Verb):
    name = "disengage"
    nick = ["calm"]
    noise = ("a", "an", "the", "down")
