# coding: utf-8

import math


from ..dn import DN
from ..roll import Roll, roll
from ..damage import Generic as GenericDamage, Damage

STANDARD = Roll("3d6")


class BaseBonus:
    ifactor = 10.0
    dfactor = 2.0
    pfactor = 1.0
    v = None

    @property
    def fbonus(self):
        return self.pfactor * ((self.v - self.ifactor) / self.dfactor)

    @property
    def bonus(self):
        b = self.fbonus
        return math.ceil(b) if b >= 0 else math.floor(b)

    @property
    def rtxt(self):
        b = self.bonus
        if b > 0:
            return f"1d20+{self.bonus}"
        if b < 0:
            return f"1d20{self.bonus}"
        return f"1d20"

    def roll(self):
        return roll(self.rtxt)

    def __str__(self):
        return f"{self.__class__.__name__}[{self.rtxt}]"

    __repr__ = __str__


class PrimaryStat(DN, BaseBonus):
    class Meta:
        units = "stat = []"

    def __init__(self, start=STANDARD):
        super().__init__(start)


class Sci(PrimaryStat):
    class Meta:
        units = "Science = [] = sci"

    d = "skill with research, problem solving, and critical thinking"


class Dip(PrimaryStat):
    class Meta:
        units = "Diplomacy = [] = dip"

    d = "ability to convince and manipulate"


class Mar(PrimaryStat):
    class Meta:
        units = "Martial = [] = mar"

    d = "fighting skills"


class Eng(PrimaryStat):
    class Meta:
        units = "Engineering = [] = eng"

    d = "skill with math, technology, and machines"


class Mor(PrimaryStat):
    class Meta:
        units = "Morale = [] = mor"

    d = "outlook on life and the current situation"


class HitPoints(DN):
    class Meta:
        units = "hitpoints = [] = HP"

    d = "damage that can be taken"

    @classmethod
    def affinity_class(cls, other):
        if issubclass(other, (GenericDamage, Damage)):
            return cls


class ClassRank(DN):
    class Meta:
        units = "rank = []"

    d = "class rank, based on experience"


class ExperiencePoints(DN):
    class Meta:
        units = "ExperiencePoints = [] = xp"

    d = "points awarded from experiencing combat and other risks"


class Initiative(BaseBonus):
    def __init__(self, mar, mor, mass):
        self.mar = mar
        self.mor = mor
        self.mass = mass

    @property
    def pfactor(self):
        return (self.mass / "64 kg").v

    @property
    def v(self):
        return 0.65 * self.mar.v + 0.45 * self.mor.v
