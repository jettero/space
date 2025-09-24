# coding: utf-8

from .cell import Cell
from ...door import Door as BaseDoor

class Door(BaseDoor, Cell):
    # Cell already implements container behavior for map tiles; BaseDoor adds
    # open/locked/stuck semantics and abbr.
    def __init__(self, *items, mobj=None, pos=None, open=True, locked=False, stuck=False):
        Cell.__init__(self, *items, mobj=mobj, pos=pos)
        BaseDoor.__init__(self, open=open, locked=locked, stuck=stuck)
