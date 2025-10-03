# coding: utf-8

from space.size import Mass, Volume
from space.container import Container, Containable
from space.vv import VV
from space.pv import INFINITY


class Thingy(Containable):
    class Meta:
        mass = 0.1
        volume = 0.25

    def __init__(self, x=None):
        super(Thingy, self).__init__()
        self.x = x


class BagOfHolding(Container):
    pass


class Sack(Container):
    class Meta(Container.Meta):
        mass_capacity = 5
        volume_capacity = 5


def test_contents():
    assert Container.Capacity is not BagOfHolding.Capacity
    assert Container.Capacity is not Sack.Capacity
    assert BagOfHolding.Capacity is not Sack.Capacity
    assert Container.Capacity.Meta is not BagOfHolding.Capacity.Meta
    assert Container.Capacity.Meta is not Sack.Capacity.Meta
    assert BagOfHolding.Capacity.Meta is not Sack.Capacity.Meta

    t1 = Thingy(1)
    t2 = Thingy(2)
    t3 = Thingy(3)
    t4 = Thingy(4)

    c = Sack(t1, t2)
    h = BagOfHolding(t3, t4)

    minf = Mass(INFINITY)
    vinf = Volume(INFINITY)

    assert c.capacity == VV("5kg", "5m³")
    assert h.capacity == VV(minf, vinf)

    assert t1 in c
    assert t2 in c
    assert t3 in h
    assert t4 in h

    assert c.remaining_capacity == VV("4.8kg", "4.5m³")
    assert h.remaining_capacity == VV(minf, vinf)
