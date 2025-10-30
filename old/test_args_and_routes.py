# coding: utf-8
# pylint: disable=invalid-name

import logging
import pytest

from space.args import safe_execute
from space.router import MethodNameRouter
from collections import deque

import space.exceptions as E

log = logging.getLogger(__name__)


class Ordering(deque):
    def append(self, thing):
        super().append(thing)
        log.debug("ordering.append(%s)", thing)

    def clear(self):
        super().clear()
        log.debug("ordering.clear()")

    def __str__(self):
        return " ".join(self)


ordering = Ordering()


def f1(x, y, z):
    return x, y, z


def f2(x, y, *z):
    return (
        x,
        y,
    ) + z


def f3(x, y, z="def-z", **kw):
    r = {"x": x, "y": y, "z": z}
    for k in kw:
        r["_" + k] = kw[k]
    return r


class Thing:
    def f1(self, x, y, z):
        ordering.append("f1")
        return x, y, z

    def can_blah(self):
        ordering.append("cb")
        return (True, {"w0": 0})

    def can_blah_w1(self, w1):
        ordering.append("cbw1")
        return (True, {"w1": w1})

    def can_blah_w2_w1(self, w1, w2):
        ordering.append("cbw2w1")
        return (True, {"w12": w1 + w2})

    def can_blah_w1_w3(self, w3, w1):
        ordering.append("cbw1w2")
        return (True, {"w13": w3 + w1})


@pytest.fixture
def T():
    return Thing()


def test_method_router(T):
    mr = MethodNameRouter(T, "can_blah", multi=True)

    ms = set(m for m in dir(T) if m.startswith("can_blah"))
    assert set(mr.count(["w1", "w2", "w3"])) == ms
    assert set(mr.count(["w1"])) == {"can_blah", "can_blah_w1"}

    ordering.clear()
    assert mr(w1=1) == (True, {"w0": 0, "w1": 1})
    assert str(ordering) == "cbw1 cb"

    ordering.clear()
    assert mr(w2=2) == (True, {"w0": 0, "w2": 2})
    assert str(ordering) == "cb"

    ordering.clear()
    assert mr(w1=3, w2=4) == (True, {"w0": 0, "w1": 3, "w2": 4, "w12": 7})
    assert str(ordering) == "cbw2w1 cbw1 cb"


def test_f1s(T):
    assert safe_execute(f1, 1, 2, 3) == (1, 2, 3)
    assert safe_execute(T.f1, 1, 2, 3) == (1, 2, 3)
    assert safe_execute(f1, x=1, y=2, z=3) == (1, 2, 3)
    assert safe_execute(T.f1, x=1, y=2, z=3) == (1, 2, 3)


def test_f1_f2():
    assert safe_execute(f1, x=1, y=2, z=(3, 4)) == (1, 2, (3, 4))
    assert safe_execute(f2, x=1, y=2, z=(3, 4)) == (1, 2, 3, 4)


def test_f3():
    assert safe_execute(f3, 1, 2, 3, w=4) == {"x": 1, "y": 2, "z": 3, "_w": 4}
    assert safe_execute(f3, 1, y=2, z=3) == {"x": 1, "y": 2, "z": 3}


def test_icky_f1():
    with pytest.raises(E.UnfilledArgumentError, match=r"'x'.*'y'.*'z'"):
        safe_execute(f1)
    with pytest.raises(E.UnfilledArgumentError, match=r"'x'.*'y'.*'z'"):
        safe_execute(f1, z=3)
