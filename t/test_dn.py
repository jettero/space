# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name

import math

from space.pv import PV
from space.dn import DN, DescriptiveNumber  # DescriptiveNumber = DN
from space.roll import Roll


class D(DN):
    class Meta:
        units = "dd = [] = D"


class E(DescriptiveNumber):
    class Meta:
        units = "ee = [] = E"


class F(E):
    class Meta:
        units = "ff = [] = F"


c = DN(6)
d = D(7)
e = E(8)
f = F(9)


def test_str():
    assert str(c) == "6 dn"
    assert str(d) == "7 D"
    assert str(e) == "8 E"
    assert str(f) == "9 F"


def test_repr():
    assert repr(c) == "DN<6 dn>"
    assert repr(d) == "D<7 D>"
    assert repr(e) == "E<8 E>"
    assert repr(f) == "F<9 F>"


def test_desc():
    assert DN(77).desc == "supposedly descriptive number"


def test_binops():
    assert d == 7
    assert e == 8


def test_add():
    assert c + d + e + f == DN(6 + 7 + 8 + 9)
    assert sum([c, d, e, f], DN(0)) == 30


def test_nesting():
    a = DN(7)
    b = DN(a)
    assert b.v == 7


def test_dn_roller():
    for _ in range(20):
        d = DN("1d6+2")
        assert d >= 3
        assert d <= 8

    r = Roll("1d4")
    for _ in range(20):
        assert 1 <= DN(r) <= 4


def test_units():
    class Length(DN):
        class Meta:
            convert_on_set = True
            units = "m"

    l1 = Length(4)
    l2 = Length(4)
    l3 = Length(4)

    assert l1 * l2 * l3 == PV("64 m³")


def test_plus_const():
    a = DN(7)
    b = a + 1
    assert a.__class__ == b.__class__


def test_times_const():
    a = DN(7)
    b = a * 1
    assert a.__class__ == b.__class__


def test_times_const():
    a = DN(float("inf"))
    b = a * 0
    assert not math.isnan(b.v)
