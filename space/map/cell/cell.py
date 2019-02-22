# coding: utf-8

from .base import MapObj
from ...container import Container, INFINITY, ContainerError
from ...living import Living

class Cell(MapObj, Container):
    _override = None
    a = '.'

    class Meta:
        height = '10ft'
        width  = '5ft'
        depth  = '5ft'
        mass = INFINITY

    def __init__(self, *items, mobj=None, pos=None):
        Container.__init__(self, *items)
        MapObj.__init__(self, mobj=mobj, pos=pos)

    def accept(self, item):
        for item in self:
            if isinstance(item, Living):
                raise ContainerError(f'{item} is already there')
        return True

    @property
    def abbr(self):
        if self._override is not None:
            return self._override
        bi = self.biggest_item
        if bi is None:
            return self.a
        return bi.abbr

    @abbr.setter
    def abbr(self, v):
        self._override = v
