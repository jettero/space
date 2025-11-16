# coding: utf-8

import logging
import pytest
import types
from space.signals import emits_signal, subscribes_signal, get_signal

log = logging.getLogger(__name__)

SIGNAL_NAME = "floofed"


class blah:
    name = None

    def cmsg(self):
        log.debug("created %s", self)

    def __str__(self):
        return f"{self.__class__.__name__}<{self.name}>"

    __repr__ = __str__


class Emitter(blah):
    def __init__(self, name="floof"):
        self.name = name
        self.cmsg()

    @emits_signal(SIGNAL_NAME)
    def method_that_emits(self):
        return self.name


class Mob1(blah):
    def __init__(self, name):
        self.heard = list()
        self.name = name
        self.cmsg()

    def receive_signal(self, emission):
        self.heard.append(emission)


@subscribes_signal(SIGNAL_NAME)
class Mob2(Mob1):
    pass


@pytest.fixture
def em1():
    return Emitter("em1")


@pytest.fixture
def mob1():
    return Mob1("mob1")


@pytest.fixture
def mob2():
    return Mob2("mob2")


naked_floof = list()


@subscribes_signal(SIGNAL_NAME)
def flooft(em):
    naked_floof.append(em)

def test_Mob2_is_decorated():
    assert Mob2.__name__ == 'FakeClass'
    assert isinstance(Mob2, types.FunctionType)

def test_naked_floof(em1):
    assert em1.method_that_emits() == "em1"
    assert len(naked_floof) == 1


def test_nosub_mob1(mob1, em1):
    assert em1.method_that_emits() == "em1"
    assert mob1.heard == list()


def test_sub_mob1(mob1, em1):
    sig = get_signal("floofed")
    sig.subscribe(mob1)

    assert em1.method_that_emits() == "em1"
    assert len(mob1.heard) == 1


def test_decorated_mob2(mob2, em1):
    assert em1.method_that_emits() == "em1"
    assert len(mob2.heard) == 1
