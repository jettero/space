# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest
from space.living import Human
from space.map import Room
from space.damage import Kinetic, Bludgeoning, Thermal
from space.item import BulletproofVest, PersonalShield


class Tank(Human):
    resist = {Kinetic: 0.5}


@pytest.fixture
def tank():
    Room(3, 3)[1, 1] = t = Tank()
    return t


def test_structural(tank):
    tank.hurt(Bludgeoning(4))
    assert tank.damage.v == 2
    tank.hurt(Thermal(4))
    assert tank.damage.v == 6


def test_vest(dd):
    dd.slots.torso = BulletproofVest()
    dd.hurt(Bludgeoning(4))
    assert dd.damage.v == 2
    dd.hurt(Thermal(4))
    assert dd.damage.v == 6


def test_shield(dd):
    dd.slots.belt = PersonalShield()
    dd.hurt(Thermal(4))
    assert dd.damage.v == 2
    dd.hurt(Bludgeoning(4))
    assert dd.damage.v == 6


def test_record_holds_base_type(dd):
    dd.hurt(Bludgeoning(4))
    dd.slots.torso = BulletproofVest()
    dd.hurt(Bludgeoning(4))
    assert [type(e) for e in dd.damage] == [Kinetic, Kinetic]


def test_vest_in_hand(dd):
    dd.slots.right_hand = BulletproofVest()
    dd.hurt(Bludgeoning(4))
    assert dd.damage.v == 4


def test_stacking(tank):
    tank.slots.torso = BulletproofVest()
    tank.hurt(Bludgeoning(8))
    assert tank.damage.v == 2


def test_never_zero(dd):
    dd.slots.torso = BulletproofVest()
    dd.hurt(Bludgeoning(1))
    assert dd.damage.v == 1


def test_knockout_through_vest(dd):
    dd.slots.torso = BulletproofVest()
    dd.hurt(dd.hp)
    assert not dd.conscious
