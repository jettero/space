# coding: utf-8

from .cell import Cell

class Door(Cell):
    a = '+'

    def __init__(self, *items, mobj=None, pos=None, open=True):
        super().__init__(*items, mobj=mobj, pos=pos)
        self.open = open

    @property
    def abbr(self):
        return '/' if self.open else '+'
