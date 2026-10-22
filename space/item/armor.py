# coding: utf-8

from space.stdobj import StdObj
from space.size import Volume
from space.damage import Armor, Kinetic, Thermal
from space.living.slots import TorsoWearable, Belt


class BulletproofVest(Armor, TorsoWearable, StdObj):
    s = "vest"
    l = "bulletproof vest"
    d = "A heavy vest of layered ballistic fabric."
    mass = 4
    volume = Volume("8 L")
    resist = {Kinetic: 0.5}
    armor_class = {Kinetic: 4, Thermal: 1}


class PersonalShield(Armor, Belt, StdObj):
    s = "shield"
    l = "personal shield"
    d = "A belt-mounted emitter that throws a faint shimmer around its wearer."
    mass = 1
    volume = Volume("1 L")
    resist = {Thermal: 0.5}
    armor_class = {Kinetic: 1, Thermal: 4}
