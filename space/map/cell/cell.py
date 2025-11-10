# coding: utf-8

from .base import MapObj
from ...container import Container, INFINITY
from ...living import Living

import space.exceptions as E

# various symbols for floor/corridor, etc
# ■□◦◆◇◌᛭᛫܀⁘⁙⸬


class Cell(MapObj, Container):
    _override = None
    a = "◦"
    attenuation = 0.0  # hearability loss across the barrier

    class Meta:
        height = "10ft"
        width = "5ft"
        depth = "5ft"
        mass = INFINITY

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)

    def add_item(self, item):
        super().add_item(item)
        self.map.invalidate()

    def remove_item(self, item):
        super().remove_item(item)
        self.map.invalidate()

    def accept(self, item):
        if isinstance(item, Living):
            for other in self:
                if isinstance(other, Living) and not other.active:
                    raise E.ContainerError(f"{other} is already there")
        return True

    @property
    def abbr(self):
        if self._override is not None:
            return self._override
        bi = self.biggest_item(filt=Living)
        if bi is None:
            return self.a
        return bi.abbr

    @abbr.setter
    def abbr(self, v):
        self._override = v

    @property
    def is_cell(self):
        return True

    @property
    def is_floor(self):
        return False

    @property
    def is_corridor(self):
        return False

    @property
    def has_door(self):
        return False


class Floor(Cell):
    """Room floor cell (same render as Cell)."""

    a = "·"
    attenuation = 0.0

    @property
    def is_floor(self):
        return True


class Corridor(Cell):
    """Corridor/hallway floor cell (same render as Cell)."""

    a = "܀"
    attenuation = 0.0

    @property
    def is_corridor(self):
        return True
