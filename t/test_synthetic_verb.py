# coding: utf-8

import pytest
from space.living import Living
from space.stdobj import StdObj
from space.verb import Verb, register_outside_verb
from space.parser import find_routes


MARKERS = list()


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
    return True, {"living": living}


def can_itsatest_word(actor, word: str):
    MARKERS.append(("can_itsatest_word", "word", word))
    return True, {"word": word}


def can_itsatest_word_obj(actor, word: str, obj: StdObj):
    MARKERS.append(("can_itsatest_word_obj", "word", word, "obj", obj))
    return True, {"word": word, "obj": obj}


def can_itsatest_obj_living(actor, obj: StdObj, living: Living):
    MARKERS.append(("can_itsatest_obj_living", "obj", obj, "living", living))
    return True, {"obj": obj, "living": living}


def can_itsatest_words_living(actor, words: tuple[str, ...], living: Living):
    MARKERS.append(("can_itsatest_words_living", "words", words, "living", living))
    return True, {"words": words, "living": living}


def can_itsatest_living_words(actor, living: Living, words: tuple[str, ...]):
    MARKERS.append(("can_itsatest_living_words", "living", living, "words", words))
    return True, {"living": living, "words": words}


def can_itsatest_word_living(actor, word: str, living: Living):
    MARKERS.append(("can_itsatest_word_living", "word", word, "living", living))
    return True, {"word": word, "living": living}


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


def do_itsatest_living(actor, living):
    MARKERS.append(("do_itsatest_living", "living", living))


def do_itsatest_word(actor, word):
    MARKERS.append(("do_itsatest_word", "word", word))


def do_itsatest_word_obj(actor, word, obj):
    MARKERS.append(("do_itsatest_word_obj", "word", word, "obj", obj))


def do_itsatest_obj_living(actor, obj, living):
    MARKERS.append(("do_itsatest_obj_living", "obj", obj, "living", living))


def do_itsatest_words_living(actor, words, living):
    MARKERS.append(("do_itsatest_words_living", "words", words, "living", living))


def do_itsatest_living_words(actor, living, words):
    MARKERS.append(("do_itsatest_living_words", "living", living, "words", words))


def do_itsatest_word_living(actor, word, living):
    MARKERS.append(("do_itsatest_word_living", "word", word, "living", living))


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


def test_nicknames_quick(me):
    MARKERS.clear()
    assert me.do("itsatest") is True
    assert me.do("itsa") is True
    assert MARKERS == [("can_itsatest",), ("do_itsatest",), ("can_itsatest",), ("do_itsatest",)]


def test_method_scores(me):
    scores = {x.name: x.score for x in find_routes(me, "itsatest")}
    assert scores["itsatest_living"] > scores["itsatest_obj"] > scores["itsatest_words"] > scores["itsatest"]
    assert scores["itsatest_obj_living"] > scores["itsatest_obj"]
    assert scores["itsatest_word_living"] > scores["itsatest_word"]
    assert scores["itsatest_obj_words"] > scores["itsatest_obj"] > scores["itsatest_word"]
    assert scores["itsatest_words_obj"] > scores["itsatest_obj"] > scores["itsatest_words"]
    assert scores["itsatest_words_obj_words"] > scores["itsatest_words_obj"]
    assert scores["itsatest_living_words"] > scores["itsatest_living"] > scores["itsatest_words"]
    assert scores["itsatest_words_living"] > scores["itsatest_words"]
    assert scores["itsatest_words"] < scores["itsatest_word"]

@pytest.mark.parametrize('n', range(10))
def test_method_routes_by_args(me, n):
    for route in find_routes(me, "itsatest", n):
        assert route.nargs == n or (route.variadic and route.nargs <=n)


TABLE = [
    (
        "itsatest",
        ("can_itsatest",),
        ("do_itsatest",),
    ),
    (
        "itsatest foo bar",
        ("can_itsatest_words", "words", ("foo", "bar")),
        ("do_itsatest_words", "words", ("foo", "bar")),
    ),
    (
        "itsatest ubi",
        ("can_itsatest_obj", "obj", "objs.ubi"),
        ("do_itsatest_obj", "obj", "objs.ubi"),
    ),
    (
        "itsatest ubi booooing",
        ("can_itsatest_obj_words", "obj", "objs.ubi", "words", ("booooing",)),
        ("do_itsatest_obj_words", "obj", "objs.ubi", "words", ("booooing",)),
    ),
    (
        "itsatest stupid",
        ("can_itsatest_living", "living", "objs.stupid"),
        ("do_itsatest_living", "living", "objs.stupid"),
    ),
    (
        "itsatest bananas",
        ("can_itsatest_word", "word", "bananas"),
        ("do_itsatest_word", "word", "bananas"),
    ),
    (
        "itsatest bananas ubi",
        ("can_itsatest_word_obj", "word", "bananas", "obj", "objs.ubi"),
        ("do_itsatest_word_obj", "word", "bananas", "obj", "objs.ubi"),
    ),
    (
        "itsatest ubi stupid",
        ("can_itsatest_obj_living", "obj", "objs.ubi", "living", "objs.stupid"),
        ("do_itsatest_obj_living", "obj", "objs.ubi", "living", "objs.stupid"),
    ),
    (
        "itsatest stupid foo bar",
        ("can_itsatest_living_words", "living", "objs.stupid", "words", ("foo", "bar")),
        ("do_itsatest_living_words", "living", "objs.stupid", "words", ("foo", "bar")),
    ),
    (
        "itsatest foo bar stupid",
        ("can_itsatest_words_living", "words", ("foo", "bar"), "living", "objs.stupid"),
        ("do_itsatest_words_living", "words", ("foo", "bar"), "living", "objs.stupid"),
    ),
    (
        "itsatest stupid foo bar",
        ("can_itsatest_living_words", "living", "objs.stupid", "words", ("foo", "bar")),
        ("do_itsatest_living_words", "living", "objs.stupid", "words", ("foo", "bar")),
    ),
    (
        "itsatest bananas stupid",
        ("can_itsatest_word_living", "word", "bananas", "living", "objs.stupid"),
        ("do_itsatest_word_living", "word", "bananas", "living", "objs.stupid"),
    ),
    (
        "itsatest foo bar ubi",
        ("can_itsatest_words_obj", "words", ("foo", "bar"), "obj", "objs.ubi"),
        ("do_itsatest_words_obj", "words", ("foo", "bar"), "obj", "objs.ubi"),
    ),
    (
        "itsatest goom foo bar ubi bar baz goom",
        (
            "can_itsatest_words_obj_words",
            "words",
            ("goom", "foo", "bar"),
            "obj",
            "objs.ubi",
            "words",
            ("bar", "baz", "goom"),
        ),
        (
            "do_itsatest_words_obj_words",
            "words",
            ("goom", "foo", "bar"),
            "obj",
            "objs.ubi",
            "words",
            ("bar", "baz", "goom"),
        ),
    ),
]


@pytest.mark.parametrize("cmd, can_marker, do_marker", TABLE)
def test_itsatest_parametric(me, objs, cmd, can_marker, do_marker):
    msg = f'''<param>
    cmd={cmd}
    can_marker={can_marker}
    do_marker={do_marker}\n</param>'''

    def resolve(marker):
        if isinstance(marker, tuple):
            return tuple(resolve(x) for x in marker)
        if marker == "objs.ubi":
            return objs.ubi
        if marker == "objs.stupid":
            return objs.stupid
        return marker

    can_marker = resolve(can_marker)
    do_marker = resolve(do_marker)

    MARKERS.clear()
    assert me.do(cmd) is True, msg

    # me.do(cmd): parses cmd, the parser will locate all the route (see
    # find_routes), then try out combinations of args to satisfy the routes --
    # our can_ methods (above) are promiscuous AF and will pretty much allow
    # any args to work.

    CM, DM = MARKERS
    assert can_marker == CM, msg
    assert do_marker == DM, msg


def test_itsatest_coverage():
    dir_names = {n for n in dir(Living) if n.startswith("can_itsatest") or n.startswith("do_itsatest")}
    table_names = {item[0] for x in TABLE for item in x[1:]}
    assert dir_names == table_names
