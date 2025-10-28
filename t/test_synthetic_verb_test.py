# coding: utf-8

import pytest
from space.living import Living
from space.verb import Verb, register_outside_verb


# global marker store for assertions
MARKERS = []

class Action(Verb):
    name = "itsatest"
    nick = 'itsa'

register_outside_verb(Action())

def can_itsatest(actor):
    MARKERS.append(("can",))
    return True, {}

def do_itsatest(actor):
    MARKERS.append(("do",))

@pytest.fixture
def setup(me):
    me.can_itsatest = can_itsatest
    me.do_itsatest = do_itsatest
    MARKERS.clear()


def test_synthetic_verb_me_do(me,setup):
    assert me.do("itsatest") is True
    assert MARKERS == [('can',),('do',)]

