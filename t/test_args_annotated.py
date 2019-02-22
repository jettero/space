# coding: utf-8
# pylint: disable=invalid-name

import logging
import pytest

from space.args import introspect_args

log = logging.getLogger(__name__)

class N:
    def __init__(self, *a):
        self.name = ' '.join([ str(x) for x in a ])

    def __str__(self):
        return f'{self.name}'

    def __repr__(self):
        return f'{self.__class__.__name__}<{self.name}>'

    def __add__(self, other):
        return N(self, other)

class A(N):
    pass

class B(N):
    pass

class Thing:
    def f1(self, x,y,z):
        ordering.append('f1')
        return x,y,z

    def can_blah(self):
        ordering.append('cb')
        return (True, {'z': N('0')})

    def can_blah_a(self, a:A):
        ordering.append('cba')
        return (True, {'a': a})

    def can_blah_b_a(self, b:B, a:A):
        ordering.append('cbba')
        return (True, {'ab': a+b})

    def can_blah_a_n(self, n:N, a:A):
        ordering.append('cbab')
        return (True, {'an': a+n})

    def can_blah_ma(self, *ma):
        ordering.append('ma')
        return (True, {'ma': ma})

    def can_blah_oma(self, o, *ma):
        ordering.append('oma')
        return (True, {'o': o, 'ma': ma})

@pytest.fixture
def T():
    return Thing()

def test_introspect(T):
    a1 = A("A1")
    b1 = B("B1")
    n1 = N("N1")

    assert introspect_args(T.can_blah, a=a1, b=b1, n=n1) == (True, tuple(), dict())
    assert introspect_args(T.can_blah_a, a=a1, zzz=n1)   == (True, (a1,), dict())
    assert introspect_args(T.can_blah_b_a, b1, a1)       == (True, (b1,a1,), dict())
    assert introspect_args(T.can_blah_b_a, b1, b1)       == (False, (b1,), dict())
    assert introspect_args(T.can_blah_b_a, a=a1, b=a1)   == (False, tuple(), dict())
    assert introspect_args(T.can_blah_ma, ma=(1,2,3,4))  == (True, (1,2,3,4), dict())
    assert introspect_args(T.can_blah_ma)                == (False, tuple(), dict())

    assert introspect_args(T.can_blah_oma, o=1, ma=3)    == (True, (1,3), dict())
    assert introspect_args(T.can_blah_oma, 1,3)          == (True, (1,3), dict())
    assert introspect_args(T.can_blah_oma, 1)            == (False, (1,), dict())
    assert introspect_args(T.can_blah_oma, ma=3)         == (False, tuple(), dict())
