# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name

import pytest
from space.named import Named, FORMAT_RE


@pytest.fixture
def thingy(Thingy):
    return Thingy()


@pytest.fixture
def Thingy():
    class Thingy(Named):
        a = "T"
        s = "Tng"
        l = "Thingy"
        d = "a thingy"

    return Thingy


def test_named(thingy):
    assert thingy.abbr == "T"
    assert thingy.short == "Tng"
    assert thingy.long == "Thingy"
    assert thingy.desc == "Thingy :- a thingy"


def test_format_re():
    assert FORMAT_RE.match("20~a").groups() == ("20", "a")
    assert FORMAT_RE.match("20sa").groups() == ("20s", "a")
    assert FORMAT_RE.match(">20abbr").groups() == (">20", "abbr")
    assert FORMAT_RE.match("20a").groups() == ("20", "a")


def test_format(thingy):
    assert f"{thingy:20a}" == "T" + (" " * 19)


def test_tokens(Thingy):
    t1 = Thingy(abbr="T", short="Thing", long="Thing Longer")
    t2 = Thingy(abbr="T", short="Blah", long="Keymashing, Random")

    assert t1.tokens == {"thingy", "T", "thing", "longer"}
    assert t2.tokens == {"thingy", "T", "blah", "random", "keymashing"}
