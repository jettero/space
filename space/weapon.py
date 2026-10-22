# coding: utf-8

from math import ceil
from .damage import Generic, Bludgeoning


class Weapon:
    damage_type = Bludgeoning
    damage_roll = "1d2"
    attack_msg = "$N $vhit $t causing $o1 damage."
    range = None
    falloff = None

    def roll_damage(self, dist: float = 0) -> Generic:
        """
        A damage_type rolled from damage_roll.  With falloff = (cells,
        points) it loses points per cells of dist, rounded up like armor
        rounds, and never drops below 1.
        """

        d = self.damage_type(self.damage_roll)
        if self.falloff:
            cells, points = self.falloff
            return self.damage_type(max(1, ceil(d.v - points * dist / cells)))
        return d
