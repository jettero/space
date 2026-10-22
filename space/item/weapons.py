# coding: utf-8

from space.stdobj import StdObj
from space.damage import Slashing, Piercing
from space.weapon import Weapon


class Sword(Weapon, StdObj):
    s = l = "sword"
    d = "A long straight blade."
    damage_type = Slashing
    damage_roll = "1d8"
    attack_msg = "$N $vswing $o at $t causing $o1 damage."


class Katana(Sword):
    s = l = "katana"
    d = "A curved single-edged blade."
    attack_msg = "$N $vslash at $t with $o causing $o1 damage."


class Rapier(Sword):
    s = l = "rapier"
    d = "A slender blade with a needle point."
    damage_type = Piercing
    attack_msg = "$N $vthrust $o at $t causing $o1 damage."


class WireGun(Weapon, StdObj):
    s = l = "wire gun"
    d = "A stubby pistol that spits a cloud of fine wire."
    damage_type = Piercing
    damage_roll = "1d6"
    attack_msg = "$N $vfire $o at $t causing $o1 damage."
    range = 10
    falloff = (3, 1)
