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
    unusual = {
        # Grime Dice (non-transitive cycle dice):
        # https://youtu.be/6JwEYamjXpA?t=2169
        # http://www.latkin.org/blog/2015/01/16/non-transitive-grime-dice-via-mathematica/
        'red':     (4,4,4,4,4,9),
        'blue':    (2,2,2,7,7,7),
        'olive':   (0,5,5,5,5,5),
        'yellow':  (3,3,3,3,8,8),
        'magenta': (1,1,6,6,6,6),
    }

    def __init__(self, num=1, sides=6, bonus=0, unusual=None):
        if unusual is not None:
            if unusual not in self.unusual:
                raise TypeError(f'"{unusual}" die is not defined')
            sides = None
        self.u = unusual
        self.n = num
        self.d = sides
        self.b = bonus

    def roll(self, min_=1, max_=None):
        if self.u is not None:
            d = self.b
            for i in range(0, self.n):
                d += random.choice(self.faces)
            return ARoll(d, crit=False, fumb=False, min_=0, max_=None)
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
        if self.u:
            return f'{self.n}«{self.u}{self.faces}»{b}'
        return f'{self.n}d{self.d}{b}'

    @property
    def faces(self):
        if self.u is not None:
            return self.unusual[self.u]
        return tuple(range(1,self.d+1))

    @property
    def max(self):
        if self.u is not None:
            return max(self.faces) * self.n + self.b
        return self.n * self.d + self.b

    @property
    def min(self):
        if self.u is not None:
            return min(self.faces) * self.n + self.b
        return self.n + self.b

    @property
    def mean(self):
        if self.u:
            f = self.faces
            e = sum(f) / len(f)
            return self.n * e + self.b
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
        def     num(self, v): return {  'num':   int(v[0])}
        def   sides(self, v): return {'sides':   int(v[0])}
        def   bonus(self, v): return {'bonus':   int(v[0])}
        def penalty(self, v): return {'bonus':  -int(v[0])}
        def unusual(self, v): return {'unusual': str(v[0])}

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

    unusual_names = [ f'"{n}"' for n in Roller.unusual ]
    unusual_names = ' | '.join(unusual_names)

    # NOTE: we accept "red" and "olive" as names of dice;
    # and we accept "d4" and "d8" and "d7" as names of dice.
    # "d red" is not a name of a die — don't try to make it one.

    return Lark(f'''
        %import common (INT, WS)
        %ignore WS
        ?start: roller
        roller: desc
        !unusual: {unusual_names}
        desc: num? (unusual|sides) (bonus | penalty)?
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

    def __repr__(self):
        return repr(self._roller)

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
