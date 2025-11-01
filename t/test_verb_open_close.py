# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

import space.exceptions as E


@pytest.fixture
def me(objs):
    return objs.me


def test_open_door(me):
    xp = me.parse("open door")
    assert xp
    assert xp.fn.__name__ == "do_open_obj"


@pytest.mark.xfail(reason="todo: would require adjective filters")
def test_open_south_door(me):
    xp = me.parse("open south door")
    assert xp
    assert xp.fn.__name__ == "do_open_word_obj"
    xp()


@pytest.mark.xfail(reason="todo: would require adjective filters")
def test_open_north_door_fail(me):
    xp = me.parse("open north door")
    assert not xp
    with pytest.raises(E.ParseError, match=r"no door to the north"):
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
