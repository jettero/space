# coding: utf-8

from .cell import Corridor
from ...container import Container
from ...living import Living
from ...door import Door
import space.exceptions as E

class BlockedCell(Corridor):

    def __init__(self, *items, mobj=None, pos=None):
        super().__init__(*items, mobj=mobj, pos=pos)
        Container._add_item(self, Door(attached=True))

    @property
    def abbr(self):
        for it in self:
            if isinstance(it, Door):
                return '□' if it.open else '■'
        return super().abbr

    @property
    def has_door(self):
        for it in self:
            if isinstance(it, Door) and getattr(it, 'attached', False):
                return True
        return False

    def accept(self, item):
        if isinstance(item, Living):
            for it in self:
                if isinstance(it, Door) and not it.open:
                    raise E.ContainerError('the door is closed')
        return super().accept(item)
