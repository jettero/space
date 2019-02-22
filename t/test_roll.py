# coding: utf-8
# pylint: disable=invalid-name

import pytest
from space.roll import Roll

def test_roll():
    r = Roll('1d6+2')
    T = [ r.roll() for _ in range(5000) ]
    assert min(T) == 3
    assert max(T) == 8

    for x in T:
        if x == 8: assert x.crit is True
        if x.crit: assert x == 8
        if x == 3: assert x.fumb is True
        if x.fumb: assert x == 3

def test_min_max_mean():
    r = Roll('8d20+7')
    bfm = sum([ r.roll() for _ in range(50000) ]) / 50000
    assert r.min == 8 + 7
    assert r.max == 8*20 + 7
    assert pytest.approx(r.mean, rel=0.1) == bfm
