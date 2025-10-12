# coding: utf-8

import random
from lark import Lark, Transformer
from lark.exceptions import LarkError
import space.exceptions as E


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
        "red": (4, 4, 4, 4, 4, 9),
        "blue": (2, 2, 2, 7, 7, 7),
        "olive": (0, 5, 5, 5, 5, 5),
        "yellow": (3, 3, 3, 3, 8, 8),
        "magenta": (1, 1, 6, 6, 6, 6),
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
        if self.b > 0:
            b = f"+{self.b}"
        elif self.b < 0:
            b = f"{self.b}"
        else:
            b = ""
        if self.u:
            return f"{self.n}«{self.u}{self.faces}»{b}"
        return f"{self.n}d{self.d}{b}"

    @property
    def faces(self):
        if self.u is not None:
            return self.unusual[self.u]
        return tuple(range(1, self.d + 1))

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
        return self.n * 0.5 * (self.d + 1) + self.b
        # In [12]: from space.roll import Roller
        #     ...: r = Roller(8,20,7)
        #     ...: [ r.mean, sum([ r.roll() for _ in range(50000) ]) / 50000 ]
        # Out[12]: [91.0, 91.02216]


def _lark():
    class MakeRoller(Transformer):
        def num(self, v):
            return {"num": int(v[0])}

        def sides(self, v):
            return {"sides": int(v[0])}

        def bonus(self, v):
            return {"bonus": int(v[0])}

        def penalty(self, v):
            return {"bonus": -int(v[0])}

        def unusual(self, v):
            return {"unusual": str(v[0])}

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

    unusual_names = [f'"{n}"' for n in Roller.unusual]
    unusual_names = " | ".join(unusual_names)

    # NOTE: we accept "red" and "olive" as names of dice;
    # and we accept "d4" and "d8" and "d7" as names of dice.
    # "d red" is not a name of a die — don't try to make it one.

    return Lark(
        f"""
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
    """,
        parser="lalr",
        transformer=MakeRoller(),
        debug=True,
    ).parse


_lark = _lark()  # pylint: disable=invalid-name


class RollError(ValueError):
    pass


class Roll:
    def __init__(self, desc):
        try:
            desc = int(desc)
            self._roller = Roller(0, 0, desc)
            return
        except ValueError:
            pass
        try:
            self._roller = _lark(desc)
        except LarkError as e:
            raise RollError() from e

    def __repr__(self):
        return repr(self._roller)

    def __call__(self):
        """Allow instances to be called like functions to roll.

        Example: r = Roll('1d10'); r() == r.roll()
        """
        return self.roll()

    def roll(self):
        try:
            return self._roller.roll()
        except LarkError as e:
            raise RollError() from e

    # Comparison operators trigger a roll and compare its value.
    def __eq__(self, other):
        return self.roll() == other

    def __ne__(self, other):
        return self.roll() != other

    def __lt__(self, other):
        return self.roll() < other

    def __le__(self, other):
        return self.roll() <= other

    def __gt__(self, other):
        return self.roll() > other

    def __ge__(self, other):
        return self.roll() >= other

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


class Check:
    """Boolean-like roll expression with simple comparisons.

    Examples:
    - "1d10=1"  → True when a 1 is rolled
    - "1d10<2"  → True when result < 2
    - "1d10>9"  → True when result > 9
    - "1d10={3..5,2}" → True when result is in {2,3,4,5}
    """

    def __init__(self, desc):
        self.text = str(desc)
        # Very small parser: split into left roll and a right predicate.
        # Supported operators: =, !=, <, <=, >, >=, :{a,b,c}
        s = self.text

        # DC phrase: "<Stat> DC <INT>" (case-insensitive)
        self._is_dc = False
        low = s.lower()
        if " dc " in low:
            parts = s.split()
            if len(parts) == 3 and parts[1].lower() == "dc":
                self._is_dc = True
                self._stat = parts[0].lower()
                self._dc = int(parts[2])
                return

        # set membership forms: "<roll>={a,b,c}" or ranges "{3..5,2}", and negation "!={...}"
        if ("={" in s or "!={" in s) and s.endswith("}"):
            if "!={" in s:
                left, right = s.split("!=", 1)
                set_op = "!=set"
            else:
                left, right = s.split("=", 1)
                set_op = "=set"
            self._roll = Roll(left.strip())
            inner = right.strip()
            assert inner[0] == "{" and inner[-1] == "}"
            parts = [p.strip() for p in inner[1:-1].split(",") if p.strip()]
            values = []
            for p in parts:
                if ".." in p:
                    a, b = p.split("..", 1)
                    a = int(a)
                    b = int(b)
                    lo = min(a, b)
                    hi = max(a, b)
                    values.extend(range(lo, hi + 1))
                else:
                    values.append(int(p))
            self._op = set_op
            # store as tuple for immutability
            self._values = tuple(values)
            return

        # comparison forms
        # try longest operators first to avoid prefix issues
        for op in ("<=", ">=", "!=", "=", "<", ">"):
            if op in s:
                left, right = s.split(op, 1)
                self._roll = Roll(left.strip())
                self._op = op
                self._rhs = int(right.strip())
                return

        # If we get here, the expression wasn't understood.
        raise RollError()

    def __repr__(self):
        if self._is_dc:
            return f"Check({self._stat} DC {self._dc})"
        # Keep original text for non-DC forms; brief and faithful
        return f"Check({self.text})"

    def __call__(self, *args, **kwargs):
        if self._is_dc:
            return self.eval(*args)
        if args or kwargs:
            raise E.ParseError("This check does not take arguments")
        return self.eval()

    def __bool__(self):
        # For DC checks, an actor context is required.
        if self._is_dc:
            raise E.ParseError("DC check requires an actor; call the check with the actor, e.g., Check('Dip DC 10')(actor)")
        return self.eval()

    def __str__(self):
        return self.text

    def eval(self, *args):
        if self._is_dc:
            if not args:
                raise E.ParseError("DC check requires an actor argument")
            actor = args[0]
            attr = self._stat
            # direct attribute access; raise if missing
            try:
                from .living.stats import BaseBonus  # local import to avoid cycle
            except Exception as exc:  # pragma: no cover
                raise
            try:
                stat = getattr(actor, attr)
            except AttributeError as exc:
                raise E.ParseError(f"unknown stat '{attr}' for actor") from exc
            if not isinstance(stat, BaseBonus):
                raise E.ParseError(f"stat '{attr}' is not a BaseBonus")
            v = stat.roll()
            return v >= self._dc

        if self._op == "=set":
            v = self._roll.roll()
            return v in self._values
        if self._op == "!=set":
            v = self._roll.roll()
            return v not in self._values

        v = self._roll.roll()
        op = self._op
        rhs = self._rhs
        if op == "=":
            return v == rhs
        if op == "!=":
            return v != rhs
        if op == "<":
            return v < rhs
        if op == "<=":
            return v <= rhs
        if op == ">":
            return v > rhs
        if op == ">=":
            return v >= rhs
        return False

Chance = Gate = Check

class AttrChoices:
    _ordered = tuple()

    @classmethod
    def to_choose(cls):
        s = set(dir(AttrChoices))
        for k in getattr(cls, "_ordered", list()):
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
            if isinstance(a, (list, tuple)):
                a = random.choice(a)
            if callable(a):
                a = a(target)
            setattr(target, k, a)
