#!/usr/bin/env python
# coding: utf-8

from .base import Verb
from ..msg import WHISPER


class Action(Verb):
    name = "whisper"
    noise = ()

    def do_whisper_words(self, words):
        text = words.strip()
        if text and text[-1] not in ".!?":
            text += "."
        self.simple_action('$N $vwhisper, "$O"', text, sound=WHISPER)
