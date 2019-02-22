# coding: utf-8

from space.pv import PV
from space.size import Size

def test_size():
    s = Size(3,4,5,6)
    assert s.volume == PV('120 m³')

def test_size_subclass():
    class TestSize(Size):
        class Meta:
            mass = 2.2
            height = 5.92
            width = 2.5
            depth = 0.7
    s = TestSize()
    assert s.volume == PV('5.92 m') * PV('2.5 m') * PV('0.7m')
    assert s.mass == PV('2.2kg')

    s.weight = '20lb'
    assert s.mass > '5kg'
