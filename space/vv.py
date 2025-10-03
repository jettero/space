# coding: utf-8
# pylint: disable=no-member
"""
Overloaded Vector operations with scalar kludges -- scalar operations work
column-wise, which may be unexpected.

In [6]: VV(1,2) + VV(3,4)
Out[6]: [4, 6]

Three choices for multiplication

# column wise
In [7]: VV(1,2) * VV(3,4)
Out[7]: [3, 8]

# dot product
In [8]: VV(1,2).dot(VV(3,4))
Out[8]: 11

# cross product
In [9]: VV(1,2).cross(VV(3,4))
Out[9]: [0, 0, -2]

Again, most operators are column-wise operations, even things you'd expect to
be vector multiplication.

In [11]: VV(3,4) ** 2
Out[11]: [9, 16]

"""

import operator
from .pv import PV


def _g():
    yield 0


_g = type(_g())
OUR_TYPES = (list, tuple, _g)


class VV(list):
    def __init__(self, *a):
        if len(a) == 1 and isinstance(a[0], OUR_TYPES):
            a = a[0]
        super().__init__(a)

    def copy(self):
        return self.__class__(*self)

    def floor(self):
        return self.__class__(*(int(c) for c in self))

    def ceil(self):
        return self.__class__(*(int(c + 0.999999999) for c in self))

    def sign(self):
        def ii(x):
            if x > 0:
                return 1
            if x < 0:
                return -1
            return 0

        return self.__class__(*(ii(i) for i in self))

    def as_tensor(self):
        if len(self) == 2:
            return f"{self.i:0.2f}i + {self.j:0.2f}j"
        if len(self) == 3:
            return f"{self.i:0.2f}i + {self.j:0.2f}j + {self.k:0.2f}k"
        return "VV" + repr(self)

    @property
    def any_true(self):
        for i in self:
            if i:
                return True
        return False

    @property
    def all_true(self):
        for i in self:
            if not i:
                return False
        return True

    def __bool__(self):
        return self.any_true

    @property
    def length(self):
        """the geometric length of the vector -- ie, not number of dimensions"""
        # In [6]: VV(PV('3m'), PV('4m')).length
        # Out[6]: PV<5.0 m>
        return sum(self**2) ** 0.5

    @property
    def dirmag(self):
        l = self.length
        return self / l, l

    @property
    def direction(self):
        return self / self.length

    @property
    def bigpi(self):
        """Π(VV) :- the big_pi of the vector
        this property has nicknames: area and volume"""
        try:
            v = self[0]
            for i in self[1:]:
                v *= i
            return v
        except IndexError:
            raise ValueError("undefined for 0-dimensional vectors")

    volume = area = bigpi

    def dot(self, other):
        """dot product of self and other"""
        other = self.check_vv(other)
        return sum((a * b for a, b in zip(self, other)))

    def cross(self, other):
        """cross product of self and other
        always returns three dimensions
        only works for two-dimensional and three-dimensional vectors
        """
        if not isinstance(other, (VV, tuple, list)):
            raise TypeError(f"{other} must be VV, tuple or list")

        # (a₁b₂ - a₂b₁)i + (a₂b₀ - a₀b₂)j + (a₀b₁ - a₁b₀)k

        if len(self) == 2:
            return VV(0, 0, self[0] * other[1] - self[1] * other[0])

        if len(self) == 3:
            return VV(
                self[2] * other[1] - self[1] * other[2],
                self[2] * other[0] - self[0] * other[2],
                self[0] * other[1] - self[1] * other[0],
            )

        raise ValueError("cross product only defined for len-2 and len-3")

    def intersects(self, other, close_enough=0.999999):
        """False when the projection of this vector onto that vector is nearly 1
        True otherwise"""
        if not isinstance(other, VV):
            try:
                other = other.direction
            except AttributeError:
                other = VV(*other).direction
        if abs(self.direction.dot(other)) > close_enough:
            return False  # parallel
        return True

    def check_vv(self, other):
        """given an argument, raise exceptions for type mismatches or compute an appropriate
        other vector ... e.g.:
        v1 = VV(1,2)
        v2 = v1.check_vv(3,4) # v2 is VV(3,4)
        v2 = v1.check_vv('blah') # raise TypeError

        to facilitate this:
            VV(1,2) + 3 = VV(1,2) + VV(3,3)
            VV(1,2) * 3 = VV(1,2) * VV(3,3),

        v2 = v1.check_vv(3.4) # v2 is 3.4, 3.4
        """
        if isinstance(other, (int, float, PV)):
            return VV([other] * len(self))
        if not isinstance(other, OUR_TYPES):
            raise TypeError("argument is not VV or scalar")
        if len(self) != len(other):
            raise TypeError("VV size mismatch")
        return other


def add_named_positions(letters, cls=VV):
    def gnp(i):
        def np(self):
            return self[i]

        def nps(self, v):
            self[i] = v

        return property(np).setter(nps)

    for i, n in enumerate(letters):
        setattr(cls, n, gnp(i))


add_named_positions("xyzw")
add_named_positions("ijk")


def add_binops(*ops, cls=VV):
    def _helper(op):  # pylint: disable=invalid-name
        op_f = getattr(operator, op)

        def _f(self, other):
            other = self.check_vv(other)

            def _g():
                for i, j in zip(self, other):
                    yield op_f(i, j)

            return self.__class__(_g())

        return _f

    for op in ops:
        setattr(cls, f'__{op.rstrip("_")}__', _helper(op))


def add_urnops(*ops, cls=VV):
    def _helper(op):  # pylint: disable=invalid-name
        op_f = getattr(operator, op)

        def _f(self):
            def _g():
                for i in self:
                    yield op_f(i)

            return self.__class__(_g())

        return _f

    for op in ops:
        setattr(cls, f"__{op}__", _helper(op))


# NOTE:
# we include and/or here, ... that's for bitwise '&' and '|', not 'and' and 'or' keywords
add_binops("add", "sub", "mul", "floordiv", "truediv", "mod", "pow", "and_", "or_")
add_binops("lt", "le", "eq", "ne", "ge", "gt")
add_urnops("neg", "abs")
