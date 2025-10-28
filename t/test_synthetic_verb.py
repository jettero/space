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
    MARKERS.append(("can_itsatest",))
    return True, {}


def can_itsatest_words(actor, words: tuple[str, ...]):
    MARKERS.append(("can_itsatest_words", "words", words))
    return True, {"words": words}


def can_itsatest_obj(actor, obj: StdObj):
    MARKERS.append(("can_itsatest_obj", "obj", obj))
    return True, {"obj": obj}


def can_itsatest_obj_words(actor, obj: StdObj, words: tuple[str, ...]):
    MARKERS.append(("can_itsatest_obj_words", "obj", obj, "words", words))
    return True, {"obj": obj, "words": words}


def can_itsatest_living(actor, living: Living):
    MARKERS.append(("can_itsatest_living", "living", living))
    return True, {"target": living}


def can_itsatest_word(actor, word: str):
    MARKERS.append(("can_itsatest_word", "word", word))
    return True, {"word": word}


def can_itsatest_word_obj(actor, word: str, obj: StdObj):
    MARKERS.append(("can_itsatest_word_obj", "word", word, "obj", obj))
    return True, {"word": word, "obj": obj}


def can_itsatest_obj_living(actor, obj: StdObj, living: Living):
    MARKERS.append(("can_itsatest_obj_living", "obj", obj, "living", living))
    return True, {"obj": obj, "target": living}


def can_itsatest_words_living(actor, words: tuple[str, ...], living: Living):
    MARKERS.append(("can_itsatest_words_living", "words", words, "living", living))
    return True, {"words": words, "target": living}


def can_itsatest_living_words(actor, living: Living, words: tuple[str, ...]):
    MARKERS.append(("can_itsatest_living_words", "living", living, "words", words))
    return True, {"target": living, "words": words}


def can_itsatest_word_living(actor, word: str, living: Living):
    MARKERS.append(("can_itsatest_word_living", "word", word, "living", living))
    return True, {"word": word, "target": living}


def can_itsatest_words_obj(actor, words: tuple[str, ...], obj: StdObj):
    MARKERS.append(("can_itsatest_words_obj", "words", words, "obj", obj))
    return True, {"words": words, "obj": obj}


def can_itsatest_words_obj_words(actor, words: tuple[str, ...], obj: StdObj, more: tuple[str, ...]):
    MARKERS.append(("can_itsatest_words_obj_words", "words", words, "obj", obj, "words", more))
    return True, {"words": words, "obj": obj, "more": more}


Living.can_itsatest = can_itsatest
Living.can_itsatest_words = can_itsatest_words
Living.can_itsatest_obj = can_itsatest_obj
Living.can_itsatest_obj_words = can_itsatest_obj_words
Living.can_itsatest_living = can_itsatest_living
Living.can_itsatest_word = can_itsatest_word
Living.can_itsatest_word_obj = can_itsatest_word_obj
Living.can_itsatest_obj_living = can_itsatest_obj_living
Living.can_itsatest_words_living = can_itsatest_words_living
Living.can_itsatest_living_words = can_itsatest_living_words
Living.can_itsatest_word_living = can_itsatest_word_living
Living.can_itsatest_words_obj = can_itsatest_words_obj
Living.can_itsatest_words_obj_words = can_itsatest_words_obj_words


def do_itsatest(actor):
    MARKERS.append(("do_itsatest",))


def do_itsatest_words(actor, words):
    MARKERS.append(("do_itsatest_words", "words", words))


def do_itsatest_obj(actor, obj):
    MARKERS.append(("do_itsatest_obj", "obj", obj))


def do_itsatest_obj_words(actor, obj, words):
    MARKERS.append(("do_itsatest_obj_words", "obj", obj, "words", words))


def do_itsatest_living(actor, target):
    MARKERS.append(("do_itsatest_living", "living", target))


def do_itsatest_word(actor, word):
    MARKERS.append(("do_itsatest_word", "word", word))


def do_itsatest_word_obj(actor, word, obj):
    MARKERS.append(("do_itsatest_word_obj", "word", word, "obj", obj))


def do_itsatest_obj_living(actor, obj, target):
    MARKERS.append(("do_itsatest_obj_living", "obj", obj, "living", target))


def do_itsatest_words_living(actor, words, target):
    MARKERS.append(("do_itsatest_words_living", "words", words, "living", target))


def do_itsatest_living_words(actor, target, words):
    MARKERS.append(("do_itsatest_living_words", "living", target, "words", words))


def do_itsatest_word_living(actor, word, target):
    MARKERS.append(("do_itsatest_word_living", "word", word, "living", target))


def do_itsatest_words_obj(actor, words, obj):
    MARKERS.append(("do_itsatest_words_obj", "words", words, "obj", obj))


def do_itsatest_words_obj_words(actor, words, obj, more):
    MARKERS.append(("do_itsatest_words_obj_words", "words", words, "obj", obj, "words", more))


Living.do_itsatest = do_itsatest
Living.do_itsatest_words = do_itsatest_words
Living.do_itsatest_obj = do_itsatest_obj
Living.do_itsatest_obj_words = do_itsatest_obj_words
Living.do_itsatest_living = do_itsatest_living
Living.do_itsatest_word = do_itsatest_word
Living.do_itsatest_word_obj = do_itsatest_word_obj
Living.do_itsatest_obj_living = do_itsatest_obj_living
Living.do_itsatest_words_living = do_itsatest_words_living
Living.do_itsatest_living_words = do_itsatest_living_words
Living.do_itsatest_word_living = do_itsatest_word_living
Living.do_itsatest_words_obj = do_itsatest_words_obj
Living.do_itsatest_words_obj_words = do_itsatest_words_obj_words


def test_synthetic_verb_me_do(me):
    MARKERS.clear()
    assert me.do("itsatest") is True
    assert me.do("itsa") is True
    assert MARKERS == [("can_itsatest",), ("do_itsatest",), ("can_itsatest",), ("do_itsatest",)]


def test_synthetic_verb_can_words(me):
    MARKERS.clear()
    assert me.do("itsatest foo bar") is True
    assert ("can_itsatest_words", "words", ("foo", "bar")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [("do_itsatest_words", "words", ("foo", "bar"))]


def test_synthetic_verb_can_obj(me, objs):
    MARKERS.clear()
    assert me.do("itsatest ubi north") is True
    assert ("can_itsatest_obj_words", "obj", objs.ubi, "words", ("north",)) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [
        ("do_itsatest_obj_words", "obj", objs.ubi, "words", ("north",))
    ]


def test_synthetic_verb_env_variants(me, objs):
    MARKERS.clear()
    assert me.do("itsatest foo bar") is True
    assert ("can_itsatest_words", "words", ("foo", "bar")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [("do_itsatest_words", "words", ("foo", "bar"))]


def test_synthetic_verb_living(me, objs):
    MARKERS.clear()
    assert me.do("itsatest stupid") is True
    assert any(m[:2] == ("can_itsatest_living", "living") for m in MARKERS)
    assert [m for m in MARKERS if m and m[0] == "do_itsatest_living" and m[1] == "living"]


def test_synthetic_verb_single_word_fails_without_word_handler(me):
    MARKERS.clear()
    assert me.do("itsatest banana") is False


def test_synthetic_verb_words_obj_singleton_words(me, objs):
    MARKERS.clear()
    assert me.do("itsatest banana ubi") is True
    assert ("can_itsatest_word_obj", "word", "banana", "obj", objs.ubi) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [
        ("do_itsatest_word_obj", "word", "banana", "obj", objs.ubi)
    ]


def test_synthetic_verb_obj_living(me, objs):
    MARKERS.clear()
    assert me.do("itsatest ubi stupid") is False


def test_synthetic_verb_words_living(me, objs):
    MARKERS.clear()
    assert me.do("itsatest foo bar stupid") is True
    assert ("can_itsatest_words", "words", ("foo", "bar", "stupid")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [("do_itsatest_words", "words", ("foo", "bar", "stupid"))]


def test_synthetic_verb_living_words(me, objs):
    MARKERS.clear()
    assert me.do("itsatest stupid foo bar") is True
    assert ("can_itsatest_living_words", "living", objs.stupid, "words", ("foo", "bar")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [
        ("do_itsatest_living_words", "living", objs.stupid, "words", ("foo", "bar"))
    ]


def test_synthetic_verb_word_living(me, objs):
    MARKERS.clear()
    assert me.do("itsatest bananas stupid") is True
    assert ("can_itsatest_word_living", "word", "bananas", "living", objs.stupid) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [
        ("do_itsatest_word_living", "word", "bananas", "living", objs.stupid)
    ]


def test_synthetic_verb_words_obj_reverse(me, objs):
    MARKERS.clear()
    assert me.do("itsatest foo bar ubi") is True
    assert ("can_itsatest_words", "words", ("foo", "bar", "ubi")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [("do_itsatest_words", "words", ("foo", "bar", "ubi"))]


def test_synthetic_verb_words_obj_words(me, objs):
    MARKERS.clear()
    assert me.do("itsatest foo bar ubi baz qux") is True
    assert ("can_itsatest_words_obj_words", "words", ("foo", "bar"), "obj", objs.ubi, "words", ("baz", "qux")) in MARKERS
    assert [m for m in MARKERS if m and m[0].startswith("do_")] == [
        ("do_itsatest_words_obj_words", "words", ("foo", "bar"), "obj", objs.ubi, "words", ("baz", "qux"))
    ]
