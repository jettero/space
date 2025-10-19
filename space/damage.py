# coding: utf-8

from collections import deque
import space.exceptions as E
from .dn import DN

__all__ = ["Generic", "Kinetic", "Thermal", "Mind", "Damage"]


class Generic(DN):
    d = "generic damage (type unknown)"

    class Meta:
        units = "damage = [damage]"


class Kinetic(Generic):
    s = a = "K"
    d = "damage from pysical objects"

    class Meta:
        units = "kinetic = [kinetic]"


class Thermal(Generic):
    s = a = "T"
    d = "damage from heat (aka energy)"

    class Meta:
        units = "thermal = [thermal]"


class Mind(Generic):
    s = a = "M"
    d = "damage to the spirit or morale"

    class Meta:
        units = "mind = [mind]"


class Damage:
    generic = Generic

    def __init__(self, *a):
        # do not call the super().__init__ ; it sets up .v, which we provide as a property
        self._items = deque()
        self.add(a)

    def _genericize(self, *a):
        for i in a:
            if isinstance(i, Damage):
                yield from i.items
            elif isinstance(i, (list, tuple)):
                yield from self._genericize(*i)
            elif isinstance(i, Generic):
                yield i
            else:
                try:
                    yield self.generic(i)
                except Exception as e:
                    raise E.InvalidDamageType(f"bad damage value: {repr(i)}") from e

    def add(self, amount):
        self._items.extend(self._genericize(amount))
        return self

    @property
    def items(self):
        return tuple(self)

    def __iter__(self):
        return (i.clone() for i in self._items)

    def clone(self):
        return self.__class__(self.items)

    @property
    def v(self):
        if not self._items:
            return 0
        return sum(i.v for i in self._items)

    def __add__(self, other):
        return self.clone().add(other)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.v})"

    def __str__(self):
        r = dict()
        for d in self._items:
            t = type(d)
            if t not in r:
                r[t] = d
            else:
                r[t] += d
        ret = " + ".join([x.abbr for x in r.values()])
        if len(r) > 1:
            g = self.generic(self.v)
            return f"{ret} = {g.abbr}"
        return ret

    def __bool__(self):
        for i in self._items:
            if i.v > 0:
                return True
        return False
