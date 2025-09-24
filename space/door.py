# coding: utf-8

from .obj import baseobj


class CanOpen:
    open: bool = False
    locked: bool = False
    stuck: bool = False

    def can_open(self):
        ok = not self.open and not self.locked and not self.stuck
        return ok, {}

    def do_open(self):
        self.open = True


class Door(CanOpen, baseobj):
    a = '/'
    s = 'a door'
    l = 'a simple door'

    def __init__(self, *, open=False, locked=False, stuck=False):
        super().__init__()
        self.open = bool(open)
        self.locked = bool(locked)
        self.stuck = bool(stuck)

    @property
    def abbr(self):
        return '/' if self.open else '+'
