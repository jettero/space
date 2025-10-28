# coding: utf-8

import pytest
from space.living import Living
from space.stdobj import StdObj
from space.verb import Verb, register_outside_verb


# global marker store for assertions
MARKERS = []


class Action(Verb):
    name = "itsatest"
    nick = "itsa"


register_outside_verb(Action())


def can_itsatest(actor):
    MARKERS.append(("can",))
    return True, {}


def can_itsatest_words(actor, words: tuple[str, ...]):
    MARKERS.append(("can", "words", words))
    return True, {"words": words}


def can_itsatest_obj(actor, obj: StdObj):
    MARKERS.append(("can", "obj", obj))
    return True, {"obj": obj}


def can_itsatest_obj_words(actor, obj: StdObj, words: tuple[str, ...]):
    MARKERS.append(("can", "obj", obj, "words", words))
    return True, {"obj": obj, "words": words}


def can_itsatest_living(actor, living: Living):
    MARKERS.append(("can", "living", living))
    return True, {"target": living}


Living.can_itsatest = can_itsatest
Living.can_itsatest_words = can_itsatest_words
Living.can_itsatest_obj = can_itsatest_obj
Living.can_itsatest_obj_words = can_itsatest_obj_words
Living.can_itsatest_living = can_itsatest_living


def do_itsatest(actor):
    MARKERS.append(("do",))


def do_itsatest_words(actor, words):
    MARKERS.append(("do", "words", words))


def do_itsatest_obj(actor, obj):
    MARKERS.append(("do", "obj", obj))


def do_itsatest_obj_words(actor, obj, words):
    MARKERS.append(("do", "obj", obj, "words", words))


def do_itsatest_living(actor, target):
    MARKERS.append(("do", "living", target))


Living.do_itsatest = do_itsatest
Living.do_itsatest_words = do_itsatest_words
Living.do_itsatest_obj = do_itsatest_obj
Living.do_itsatest_obj_words = do_itsatest_obj_words
Living.do_itsatest_living = do_itsatest_living


def test_synthetic_verb_me_do(me):
    MARKERS.clear()
    assert me.do("itsatest") is True
    assert me.do("itsa") is True
    assert MARKERS == [("can",), ("do",), ("can",), ("do",)]


def test_synthetic_verb_can_words(me):
    MARKERS.clear()
    assert me.do("itsatest foo bar") is True
    assert ("can", "words", ("foo", "bar")) in MARKERS
    assert [m for m in MARKERS if m and m[0] == "do"] == [("do", "words", ("foo", "bar"))]


def test_synthetic_verb_can_obj(me, objs):
    MARKERS.clear()
    assert me.do("itsatest ubi north") is True
    assert ("can", "obj", objs.ubi, "words", ("north",)) in MARKERS
    assert [m for m in MARKERS if m and m[0] == "do"] == [("do", "obj", objs.ubi, "words", ("north",))]


def test_synthetic_verb_env_variants(me, objs):
    MARKERS.clear()
    assert me.do("itsatest foo bar") is True
    assert ("can", "words", ("foo", "bar")) in MARKERS
    assert [m for m in MARKERS if m and m[0] == "do"] == [("do", "words", ("foo", "bar"))]


def test_synthetic_verb_living(me, objs):
    MARKERS.clear()
    assert me.do("itsatest stupid") is True
    assert any(m[:2] == ("can", "living") for m in MARKERS)
    assert [m for m in MARKERS if m and m[0] == "do" and m[1] == "living"]
