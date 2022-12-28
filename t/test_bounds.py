# coding: utf-8

from space.map.util import Bounds

def test_map_bounds():
    fakemap = [ range(2), range(2) ]
    b = Bounds(fakemap)
    assert b.x  == 0
    assert b.y  == 0
    assert b.X  == 1
    assert b.Y  == 1
    assert b.XX == 2
    assert b.YY == 2

def test_tuple_bounds():
    b = Bounds(1,1,3,3)
    assert b.x  == 1
    assert b.y  == 1
    assert b.X  == 3
    assert b.Y  == 3
    assert b.XX == 3
    assert b.YY == 3

def test_recompute():
    b = Bounds(0,0,10,10)
    assert b.x  == 0
    assert b.y  == 0
    assert b.X  == 10
    assert b.Y  == 10
    assert b.XX == 11
    assert b.YY == 11

    b.x = 5
    # b.recompute() # this was removed a while ago

    assert b.XX == (10-5) + 1
    assert b.YY == (10-0) + 1
