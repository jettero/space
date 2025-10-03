# coding: utf-8

from space.vv import VV
from space.pv import PV


def test_vv():
    v1 = VV(1, 2, 3)
    v2 = VV(4, 5, 6)
    v3 = v1 + v2

    assert tuple(v3) == (5, 7, 9)
    assert tuple(-v3) == (-5, -7, -9)

    v0 = VV(0, 0)
    v1 = VV(0, 1)
    v2 = VV(1, 0)
    v3 = VV(1, 1)
    vt = (v0, v1, v2, v3)

    for i in vt:
        assert v0 & i == v0
        assert v0 | i == i

    for i in vt:
        assert v3 & i == i
        assert v3 | i == v3

    assert v1 & v2 == v0
    assert v1 | v2 == v3

    assert v0.any_true is False
    assert v1.any_true is True
    assert v2.any_true is True
    assert v3.any_true is True

    assert v0.all_true is False
    assert v1.all_true is False
    assert v2.all_true is False
    assert v3.all_true is True

    assert (v3 > v1) == VV(True, False)
    assert (v1 < v3) == VV(True, False)


def test_magic_triangle():
    v1 = VV(PV("3m"), PV("4m"))
    assert v1.length == PV("5m")
    assert v1.bigpi == PV("12m²")
    assert v1.area == PV("12m²")
    v1.append("1m")
    assert v1.volume == PV("12m³")


def test_intersections():
    v1 = VV(0, 1)
    v2 = VV(1, 0)
    v3 = VV(0, 1)

    assert v1.intersects(v2)
    assert not v1.intersects(v3)
