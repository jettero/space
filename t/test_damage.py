# coding: utf-8
# pylint: disable=unidiomatic-typecheck,protected-access

from space.damage import Damage, Kinetic, Thermal, Mind, Generic


def test_damage_types():
    k = Kinetic(7)
    t = Thermal(8)
    m = Mind(9)
    g = Generic(10)

    a = (k, t, m, g)

    for l, r in zip(a, a):
        s = l + r
        t = l.v + r.v
        if l is r:
            assert s.v == l.v * 2
            assert s.v == r.v * 2
            assert s.v == t
            assert type(s) == type(l)
            assert str(s) == f"{l.v * 2} {l.s}"
        else:
            assert s == t
            assert type(s) == Generic

    mpm = m + m
    assert mpm is not m
    assert mpm == "18 mind"
    assert str(mpm) == "18 M"


def test_clone():
    d = Damage(Kinetic(3), Mind(4))
    e = d.clone()
    for i in (
        d,
        e,
    ):
        assert i.v == 7
        assert type(i) == Damage

    for i, j in zip(d._items, e._items):
        assert i is not j
        assert i == j
        assert type(i) == type(j)
        assert isinstance(i, (Kinetic, Mind))
        assert isinstance(j, (Kinetic, Mind))


def test_add():
    d = Damage()
    d.add(3)
    d.add(7)
    d.add(9)

    assert d.v == 19
    assert type(d.v) == int

    for i in (d,):
        assert isinstance(i, Damage)

    d = Damage(*[Kinetic(i) for i in range(1, 11)])
    assert d.v == 55
    assert type(d.v) == int


def test_add_and_increment():
    d = Damage(1, 2, 3, 4)
    e = d + 3
    f = e
    f += 3

    assert d is not e
    assert d is not f
    assert e is not f
    assert d.v == 10
    assert e.v == 13
    assert f.v == 16
    assert type(d) == Damage
    assert type(e) == Damage
    assert type(f) == Damage
