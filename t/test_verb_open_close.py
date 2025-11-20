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


def test_close_door(me):
    assert (xp := me.parse("open door"))
    xp()
    assert (xp := me.parse("close door"))
    assert xp.fn.__name__ == "do_close_obj"
    xp()
    assert not (xp := me.parse("move south"))
    with pytest.raises(E.ParseError, match=r"door is closed"):
        xp()


def test_close_south_door(me):
    assert (xp := me.parse("open door"))
    xp()
    assert (xp := me.parse("close south door"))
    assert xp.fn.__name__ in ("do_close_word_obj", "do_close_obj")  #  nicknamed in humanoid.py
    xp()
    assert not (xp := me.parse("move south"))
    with pytest.raises(E.ParseError, match=r"door is closed"):
        xp()
