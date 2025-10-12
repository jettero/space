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


def test_proper_name_sets_long_short_and_unique(Thingy):
    t = Thingy()
    t.proper_name = "Jordan Schitzo Blueberry"
    assert t.long == "Jordan Schitzo Blueberry"
    assert t.short == "Jordan"
    assert t.unique is True


def test_proper_name_with_tilde_sets_full_for_both(Thingy):
    t = Thingy()
    t.proper_name = "Dig~Dug"
    assert t.long == "Dig Dug"
    assert t.short == "Dig Dug"
    assert t.unique is True


def test_proper_name_falsey_resets_generic_and_not_unique(Thingy):
    t = Thingy()
    t.proper_name = None
    assert t.long == "something"
    assert t.short == "something"
    assert t.unique is False
