# coding: utf-8

from .cell import Corridor
from ...container import Container
from ...living import Living
from ...door import Door
import space.exceptions as E


class BlockedCell(Corridor):
    @property
    def attenuation(self):
        # hearability loss across the barrier, for BlockedCells, this depends on open-state
        d = self.door
        if d is None or d.open:
            return 0.0
        return 0.7

    def __init__(self, *a, **kw):
        super().__init__(*(Door(is_attached=True), *a), **kw)

    @property
    def door(self):
        for it in self:
            if isinstance(it, Door) and it.attached:
                return it

    @property
    def has_door(self):
        return bool(self.door)

    def accept(self, item):
        if isinstance(item, Living):
            if door := self.door:
                if not door.open:
                    raise E.ContainerError(f"the {door} is closed")
        return super().accept(item)

    def do_open(self):
        if door := self.door:
            if not door.open:
                return door.do_open()
            raise E.ContainerError(f"the {door} is already open")
        raise E.ContainerError(f"there is no door to open")

    def do_close(self):
        if door := self.door:
            if door.open:
                return door.do_close()
            raise E.ContainerError(f"the {door} is already closed")
        raise E.ContainerError(f"there is no door to close")
