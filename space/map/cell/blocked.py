# coding: utf-8

from .cell import Cell, Corridor
from ...container import Container
from ...door import Door
from ...util import weakify
import space.exceptions as E


class BlockedCell(Corridor):
    door_class = Door

    @property
    def attenuation(self):
        # dB lost entering the cell, for BlockedCells, this depends on open-state
        d = self.door
        return 0 if d is None or d.open else d.attenuation

    def __init__(self, *a, **kw):
        super().__init__(*(self.door_class(is_attached=True), *a), **kw)

    @property
    def door(self):
        for it in self:
            if isinstance(it, Door) and it.attached:
                return it

    @property
    def has_door(self):
        return bool(self.door)

    def accept(self, item):
        if (door := self.door) and not door.open:
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


class AirlockDoor(Door):
    l = "airlock door"
    d = "an airlock door"

    def _tokenize(self):
        return super()._tokenize() | {"hatch"}


class HatchDoor(AirlockDoor):
    def passage(self, body):
        """
        Opening the hatch from inside the airlock (the other door shut, so
        nobody outside sees it) finishes the crossing: `body` moves to the
        twin Airlock on the other map, and the door that opens is that
        airlock's inner door.  Undocked, it's just this hatch.
        """

        if (there := body.location.twin) is None:
            return self
        body.changes_view(there.add_item, body)
        return there.inner.door


class AirlockInner(BlockedCell):
    """The near door of an Airlock: the side its own map is on."""

    door_class = AirlockDoor


class Hatch(BlockedCell):
    """The far door of an Airlock: the side where the other map is."""

    door_class = HatchDoor


class Airlock(Cell):
    """
    The cell between an airlock's inner door and its Hatch.  dock() twins
    the station's airlock with the ship's; see HatchDoor.
    """

    twin = None

    @property
    def hatch(self):
        return self.neighbors(of_type=Hatch)[0]

    @property
    def inner(self):
        return self.neighbors(of_type=AirlockInner)[0]


def dock(station, ship):
    """
    Twin the Airlock on map `station` with the one on map `ship`, and
    interlock each airlock's two doors: neither opens while the other is
    open.
    """

    a, b = next(station.iter_cells(Airlock)), next(ship.iter_cells(Airlock))
    a.twin, b.twin = weakify(b), weakify(a)
    for x in (a, b):
        x.hatch.door.interlock, x.inner.door.interlock = weakify(x.inner.door), weakify(x.hatch.door)
