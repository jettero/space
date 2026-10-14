# coding: utf-8

import pytest
from space.shell.list import Shell as ListShell


@pytest.fixture
def o(objs):
    objs.me.shell = ListShell()
    objs.dig_dug.shell = ListShell()
    return objs


def test_open_door_refreshes_quietly(o):
    o.me.do("open door")
    assert o.dig_dug in o.me.shell.map_view.objects
    assert o.me.shell.msgs == ["You open a door."]


def test_move_refreshes_quietly(o):
    o.me.do("open door; move s")
    assert o.me.location.pos == (8, 2)
    assert not any("look" in m for m in o.dig_dug.shell.msgs)
    assert not any("look" in m for m in o.me.shell.msgs)
    v0 = o.me.shell.map_view
    o.me.do("move n")
    assert o.me.shell.map_view is not v0


def test_other_move_refreshes_me(o):
    o.me.do("open door")
    v0 = o.me.shell.map_view
    o.dig_dug.do("move s")
    assert o.me.shell.map_view is not v0
    assert o.dig_dug in o.me.shell.map_view.objects


def test_moved_obj_refreshes_its_viewers(o):
    assert o.dig_dug not in o.me.viewers()
    o.me.do_move_obj_words(o.dig_dug, ("s",))
    assert o.dig_dug.location.pos == (8, 4)
    assert o.dig_dug.shell.map_view is not None


def test_obj_viewers(o):
    assert o.dig_dug in o.ubi.viewers()
    assert o.me not in o.ubi.viewers()


def test_look_is_full_look(o):
    o.me.do("open door; look")
    assert o.dig_dug.shell.msgs[-1] == "Paul looks around."
    assert "[" in o.me.shell.msgs[-1]
