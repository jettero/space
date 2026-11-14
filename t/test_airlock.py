# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name

import pytest

from space.living import Human
from space.map import import_map_from_path
from space.map.cell import Floor
from space.map.cell.blocked import Airlock, dock
from space.shell.list import Shell as ListShell


@pytest.fixture
def station():
    return import_map_from_path("asset/station1.map")


@pytest.fixture
def ship(station):
    dock(station, s := import_map_from_path("asset/ship1.map"))
    return s


@pytest.fixture
def me(station, ship):
    me = Human("Bob")
    me.shell = ListShell()
    next(station.iter_cells(Airlock)).inner.neighbors(of_type=Floor)[0].add_item(me)
    return me


def test_board_and_leave(me, station, ship):
    assert me.location is station.get(59, 30)
    me.do("e")
    assert me.location is station.get(59, 30)

    me.do("open east airlock; e; e; close door; open east airlock")
    assert me.location is ship.get(1, 2), me.shell.msgs
    assert ship.get(2, 2).door.open and not station.get(60, 30).door.open
    assert me.shell.map_view.a_map is ship

    me.do("e; e; close door")
    assert me.location is ship.get(3, 2), me.shell.msgs
    assert not ship.get(2, 2).door.open, me.shell.msgs

    me.do("open west hatch; w; w; close door; open west airlock; w; w; close door")
    assert me.location is station.get(59, 30), me.shell.msgs
    assert not station.get(60, 30).door.open and not ship.get(2, 2).door.open
    assert me.shell.map_view.a_map is station


def test_change_of_mind(me, station):
    me.do("open east airlock; e; e; close west airlock; open west airlock; w; w")
    assert me.location is station.get(59, 30), me.shell.msgs


@pytest.mark.parametrize(
    "cmds,far",
    [
        ("open east airlock; e; e", "east"),
        ("open east airlock; e; e; close west airlock; open east airlock", "west"),
    ],
)
def test_interlock(me, cmds, far):
    me.do(cmds)
    here = me.location
    me.do(f"open {far} airlock")
    assert me.location is here and "won't open" in me.shell.msgs[-1], me.shell.msgs
