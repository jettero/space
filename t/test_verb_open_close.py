# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

import space.exceptions as E
from space.shell.list import Shell as ListShell


@pytest.fixture
def me(objs):
    return objs.me


@pytest.mark.parametrize(
    "cmd",
    [
        "open door",
        "open a door",
        "open the door",
        "open south door",
        "open the south door",
        "look door",
        "look at a door",
        "look south door",
        "look at the south door",
    ],
)
def test_door_phrasings(me, cmd):
    assert me.parse(cmd)


def test_open_door(me):
    xp = me.parse("open door")
    assert xp
    assert xp.fn.__name__ == "do_open_obj"


def test_open_south_door(me):
    xp = me.parse("open south door")
    assert xp
    assert xp.fn.__name__ in ("do_open_word_obj", "do_open_obj")  # nicknamed in humanoid.py
    xp()


def test_open_north_door_fail(me):
    xp = me.parse("open north door")
    assert not xp
    with pytest.raises(E.ParseError, match=r"unable to find.*north door"):
        xp()


def test_open_nonsense_fails(me):
    xp = me.parse("open nothingburger")
    assert not xp
    with pytest.raises(E.ParseError, match=r"nothingburger"):
        xp()


def test_open_nonsense_door_fails(me):
    xp = me.parse("open nothingburger door")
    assert not xp  # this shouldn't ever work


def test_open_door_and_move_through_it(me):
    xp = me.parse("move south")
    assert not xp
    assert "door is closed" in str(xp.error)
    with pytest.raises(E.ParseError, match=r"door is closed"):
        xp()

    xp = me.parse("open door")
    assert xp and xp.fn.__name__ == "do_open_obj"
    xp()

    xp = me.parse("move south")
    assert xp and xp.fn.__name__ == "do_move_words"
    xp()
    assert me.location.pos == (8, 2)


def test_open_open_door_after_someone_else_acts(me, objs):
    me.shell = ListShell()
    me.do("open door")
    objs.stupid.simple_action("$N $vgnash $p teeth.")
    me.do("open door")
    assert me.shell.msgs[-1] == "door is already open"


def test_close_closed_door(me):
    me.shell = ListShell()
    me.do("open door; close door; close door")
    assert me.shell.msgs[-1] == "door is already closed"


def test_close_door(me):
    assert (xp := me.parse("open door"))
    xp()
    assert (xp := me.parse("close door"))
    assert xp.fn.__name__ == "do_close_obj"
    xp()
    assert not (xp := me.parse("move south"))
    with pytest.raises(E.ParseError, match=r"door is closed"):
        xp()


def test_move_item_through_closed_door(me, objs, a_map):
    a_map[8, 1] = objs.ubi
    assert not (xp := me.parse("move bauble s"))
    assert "door is closed" in str(xp.error)
    assert objs.ubi.location.pos == (8, 1)


def test_place_item_in_closed_door(objs, a_map):
    with pytest.raises(E.ContainerError):
        a_map[8, 2] = objs.ubi


def test_close_door_on_item(me, objs, a_map):
    me.do("open door")
    a_map[8, 2] = objs.ubi
    assert not (xp := me.parse("close door"))
    assert "in the way" in str(xp.error)
    assert objs.door.open


def test_close_door_on_self(me):
    me.do("open door; move s")
    assert not (xp := me.parse("close door"))
    assert "You're in the way" in str(xp.error)


@pytest.mark.parametrize("cmd", ["move door n", "get door"])
def test_attached_door(me, cmd):
    assert not (xp := me.parse(cmd))
    assert "attached" in str(xp.error)


def test_close_south_door(me):
    assert (xp := me.parse("open door"))
    xp()
    assert (xp := me.parse("close south door"))
    assert xp.fn.__name__ in ("do_close_word_obj", "do_close_obj")  #  nicknamed in humanoid.py
    xp()
    assert not (xp := me.parse("move south"))
    with pytest.raises(E.ParseError, match=r"door is closed"):
        xp()
