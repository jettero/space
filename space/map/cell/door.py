# coding: utf-8

from .cell import Cell
from ...container import Container
from ...door import Door as BaseDoor
import space.exceptions as E

class Door(BaseDoor, Cell):
    # Map cell door with open/locked/stuck semantics. Renders like a cell when occupied.
    s = 'a door'
    l = 'a simple door'

    def __init__(self, *items, mobj=None, pos=None, open=False, locked=False, stuck=False):
        Cell.__init__(self, *items, mobj=mobj, pos=pos)
        BaseDoor.__init__(self, open=open, locked=locked, stuck=stuck)

    @property
    def a(self):
        return '□' if self.open else '■'

    def accept(self, item):
        if not self.open:
            raise E.ContainerError('the door is closed')
        return Container.accept(self, item)
