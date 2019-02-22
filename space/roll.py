# coding: utf-8

import random
from lark import Lark, Transformer
from lark.exceptions import LarkError

class ARoll(int):
    crit = False
    fumb = False

    def __new__(cls, v, crit=False, fumb=False, min_=1, max_=None):
        if min_ is not None:
            v = max(min_, v)
        if max_ is not None:
            v = min(max_, v)
        r = int.__new__(cls, v)
        r.crit = crit
        r.fumb = fumb
        return r

class Roller:
    def __init__(self, num=1, sides=6, bonus=0):
        self.n = num
        self.d = sides
        self.b = bonus
    def roll(self, min_=1, max_=None):
        d = self.b
        crit = True
        fumb = True
        for i in range(0, self.n):
            iv = random.randint(1, self.d)
            if iv != self.d:
                crit = False
            if iv != 1:
                fumb = False
            d += iv
        return ARoll(d, crit=crit, fumb=fumb, min_=min_, max_=max_)

    def __repr__(self):
        if self.b > 0:   b = f'+{self.b}'
        elif self.b < 0: b = f'{self.b}'
        else:            b = ''
        return f'{self.n}d{self.d}{b}'

    @property
    def max(self):
        return self.n * self.d + self.b

    @property
    def min(self):
        return self.n + self.b

    @property
    def mean(self):
        if self.n < 1:
            return self.b
        # o = list(range(1,self.d+1))
        # e = sum(o) / len(o)
        # e = 0.5 * self.d * (self.d+1) / self.d
        # e = 0.5 * (self.d+1)
        # E = self.n * e
        return self.n * 0.5 * (self.d+1) + self.b
        # In [12]: from space.roll import Roller
        #     ...: r = Roller(8,20,7)
        #     ...: [ r.mean, sum([ r.roll() for _ in range(50000) ]) / 50000 ]
        # Out[12]: [91.0, 91.02216]


def _lark():
    class MakeRoller(Transformer):
        def     num(self, v): return {  'num':  int(v[0])}
        def   sides(self, v): return {'sides':  int(v[0])}
        def   bonus(self, v): return {'bonus':  int(v[0])}
        def penalty(self, v): return {'bonus': -int(v[0])}

        def desc(self, v):
            ret = dict()
            for i in v:
                ret.update(i)
            return ret

        def roller(self, v):
            args = dict()
            for i in v:
                args.update(i)
            return Roller(**args)

    return Lark('''
        %import common (INT, WS)
        %ignore WS
        ?start: roller
        roller: desc
        desc: num? sides (bonus | penalty)?
        num: INT
        sides: "d" INT
        bonus: "+" INT
        penalty: "-" INT
    ''', parser='lalr', transformer=MakeRoller(), debug=True).parse

_lark = _lark() # pylint: disable=invalid-name

class RollError(ValueError):
    pass

class Roll:
    def __init__(self, desc):
        try:
            desc = int(desc)
            self._roller = Roller(0,0,desc)
            return
        except ValueError:
            pass
        try:
            self._roller = _lark(desc)
        except LarkError as e:
            raise RollError() from e

    def roll(self):
        try:
            return self._roller.roll()
        except LarkError as e:
            raise RollError() from e

    @property
    def mean(self):
        return self._roller.mean

    @property
    def min(self):
        return self._roller.min

    @property
    def max(self):
        return self._roller.max

def roll(desc):
    return Roll(desc).roll()

class AttrChoices:
    _ordered = tuple()

    @classmethod
    def to_choose(cls):
        s = set(dir(AttrChoices))
        for k in getattr(cls, '_ordered', list()):
            if k not in s:
                s.add(k)
                yield k
        for k in dir(cls):
            if k not in s:
                s.add(k)
                yield k

    @classmethod
    def apply_attrs(cls, target):
        for k in cls.to_choose():
            a = getattr(cls, k)
            if isinstance(a, Roll):
                a = a.roll()
            if isinstance(a, (list,tuple)):
                a = random.choice(a)
            if callable(a):
                a = a(target)
            setattr(target, k, a)
