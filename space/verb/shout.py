#!/usr/bin/env python
# coding: utf-8

from .base import Verb
from ..msg import SHOUT


class Action(Verb):
    name = "shout"
    noise = ()

    def do_shout_words(self, words):
        text = words.strip()
        if text and text[-1] not in ".!?":
            text += "!"
        self.simple_action('$N $vshout, "$O"', text, sound=SHOUT)
