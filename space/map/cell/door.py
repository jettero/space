# coding: utf-8

from .cell import Cell
from ...container import Container
import space.exceptions as E

class Door(Cell):
    # Map cell door with open/locked/stuck semantics. Renders like a cell when occupied.
    s = 'a door'
    l = 'a simple door'

    open: bool = False
    locked: bool = False
    stuck: bool = False

    def __init__(self, *items, mobj=None, pos=None, open=False, locked=False, stuck=False):
        Cell.__init__(self, *items, mobj=mobj, pos=pos)
        self.open = bool(open)
        self.locked = bool(locked)
        self.stuck = bool(stuck)

    @property
    def abbr(self):
        bi = self.biggest_item
        if bi is not None:
            return bi.abbr
        return '□' if self.open else '■'

    def can_open(self):
        ok = not self.open and not self.locked and not self.stuck
        return ok, {}

    def do_open(self):
        self.open = True

    def accept(self, item):
        if not self.open:
            raise E.ContainerError('the door is closed')
        return Container.accept(self, item)
