# coding: utf-8

from space.container import Container, Containable
from space.living.slots import HandSlot
from space.pv import INFINITY
from space.size import Mass, Volume
from space.vv import VV


class Thingy(Containable):
    mass = 0.1
    volume = 0.25

    def __init__(self, x=None):
        super().__init__()
        self.x = x


class BagOfHolding(Container): ...


class Sack(Container):
    mass_capacity = 5
    volume_capacity = 5


minf = Mass(INFINITY)
vinf = Volume(INFINITY)


def test_contents():
    t1 = Thingy(1)
    t2 = Thingy(2)
    t3 = Thingy(3)
    t4 = Thingy(4)

    c = Sack(t1, t2)
    h = BagOfHolding(t3, t4)

    assert c.capacity.size == VV("5kg", "5m³")
    assert h.capacity.size == VV(minf, vinf)

    assert t1 in c
    assert t2 in c
    assert t3 in h
    assert t4 in h

    assert c.remaining_capacity == VV("4.8kg", "4.5m³")
    assert h.remaining_capacity == VV(minf, vinf)


def test_ubi_haver_tracks_owner(objs):
    me = objs.me
    ubi = objs.ubi
    slot = me.slots.right_hand_slot
    slot.add_item(ubi)
    assert ubi.location.__class__ is HandSlot
    assert slot.owner is me
    assert ubi.haver is me
