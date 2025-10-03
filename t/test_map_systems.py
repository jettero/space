# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name

import pytest

from space.living import Human
from space.map import Room
from space.pv import PV


@pytest.fixture
def h1():
    return Human()


@pytest.fixture
def h2():
    return Human()


@pytest.fixture
def room(h1, h2):
    r = Room()
    r[3, 3].add_item(h1)
    r[6, 7].add_item(h2)
    return r


def test_find_obj(room, h1):
    l = room.find_obj(h1)
    assert l is room[3, 3]
    assert l.pos == (3, 3)

    r = room[h1]
    assert r is room[3, 3]


def get_δ(room, i1, i2, c):
    d = room.unobstructed_distance(i1, i2)
    m = PV("5ft") * c
    return (d - m).v


def test_unobstructed_distance(room, h1, h2):
    c = (3**2 + 4**2) ** 0.5
    assert get_δ(room, h1, h2, c) < 0.01

    c = 1**0.5
    for i in ((3, 4), (4, 3), (2, 3), (3, 2)):
        room[i].add_item(h2)
        assert get_δ(room, h1, h2, c) < 0.01

    c *= 2
    for i in ((3, 5), (5, 3), (1, 3), (3, 1)):
        room[i].add_item(h2)
        assert get_δ(room, h1, h2, c) < 0.01

    for i in ((2, 2), (4, 4), (1, 1), (3, 3)):
        c = 3 - i[0]
        c **= 2
        c *= 2
        c **= 0.5
        if h1.location.pos != i:
            room[i].add_item(h2)
            assert get_δ(room, h1, h2, c) < 0.01
