# coding: utf-8

from .base import Verb

class IntentionalQuit(Exception):
    pass

class Action(Verb):
    name = 'quit'

    def execute(self, me):
        raise IntentionalQuit()
