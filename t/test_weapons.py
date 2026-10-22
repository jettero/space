# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest
from space.damage import Bludgeoning, Slashing, Piercing
from space.item import Sword, Katana, Rapier, WireGun, BulletproofVest


@pytest.fixture
def ring(me, dd, ss):
    me.do("n")
    ss.do("sseee")
    dd.slots.torso = BulletproofVest()
    return me, dd, ss


def test_weapon_is_held(me):
    assert me.weapon is me
    me.slots.left_hand = s = Sword()
    assert me.weapon is s


def test_damage_types(me):
    assert type(me.roll_damage()) is Bludgeoning
    assert type(Sword().roll_damage()) is Slashing
    assert type(Katana().roll_damage()) is Slashing
    assert type(Rapier().roll_damage()) is Piercing
    assert type(WireGun().roll_damage()) is Piercing


@pytest.mark.parametrize(
    "weapon, us, them",
    [
        (None, "You punch Dig Dug causing 3 K damage.", "Paul punches {} causing 3 K damage."),
        (
            Sword,
            "You swing a sword at Dig Dug causing 3 K damage.",
            "Paul swings a sword at {} causing 3 K damage.",
        ),
        (
            Katana,
            "You slash at Dig Dug with a katana causing 3 K damage.",
            "Paul slashes at {} with a katana causing 3 K damage.",
        ),
        (
            Rapier,
            "You thrust a rapier at Dig Dug causing 3 K damage.",
            "Paul thrusts a rapier at {} causing 3 K damage.",
        ),
        (
            WireGun,
            "You fire a wire gun at Dig Dug causing 3 K damage.",
            "Paul fires a wire gun at {} causing 3 K damage.",
        ),
    ],
)
def test_attack_line(ring, weapon, us, them):
    me, dd, ss = ring
    w = me
    if weapon:
        me.slots.right_hand = w = weapon()
    w.damage_roll = "6"
    hp = dd.hp
    me.attack(dd)
    assert dd.hp == hp - 3
    assert us in me.shell.msgs
    assert them.format("you") in dd.shell.msgs
    assert them.format("Dig Dug") in ss.shell.msgs


def test_range(me, dd):
    assert not me.can_attack_living(dd)[0]
    me.slots.right_hand = g = WireGun()
    assert me.can_attack_living(dd)[0]
    g.range = 2
    assert me.can_attack_living(dd) == (False, {"error": "Dig Dug is out of range"})


def test_out_of_sight(objs):
    objs.me.slots.right_hand = WireGun()
    assert objs.me.can_attack_living(objs.dig_dug) == (False, {"error": "You can't see Dig Dug"})


def test_falloff():
    g = WireGun()
    g.damage_roll = "6"
    assert [g.roll_damage(d).v for d in (0, 3, 9, 30)] == [6, 5, 3, 1]
