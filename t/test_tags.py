# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,pointless-statement,protected-access

import pytest

from space.named import Tags


@pytest.fixture
def some_tags():
    return Tags("t1", "t2", can={"t3", "t4"})


def test_tags(some_tags):
    assert "t1" in some_tags
    assert "t2" in some_tags
    assert "t3" not in some_tags
    assert "t4" not in some_tags


def test_clone(some_tags):
    a_clone = some_tags.clone()

    assert some_tags == a_clone
    assert some_tags._a == a_clone._a
    assert some_tags._c == a_clone._c

    assert some_tags is not a_clone
    assert some_tags._a is not a_clone._a
    assert some_tags._c is not a_clone._c


def test_add(some_tags):
    t2 = some_tags + "t3"
    assert "t3" in t2
    assert "t3" not in some_tags
    assert t2 is not some_tags
    assert t2 == {"t1", "t2", "t3"}


def test_remove(some_tags):
    t2 = some_tags - "t1"
    assert "t1" not in t2
    assert "t2" in some_tags
    assert t2 is not some_tags
    assert t2 == {
        "t2",
    }


def test_borked(some_tags):
    with pytest.raises(ValueError):
        some_tags + "borked"


def test_add_remove(some_tags):
    some_tags.add("t4")
    some_tags.remove("t3")
    assert some_tags == {"t1", "t2", "t4"}


def test_nocan():
    tags = Tags("t1")
    tags += "t2"
    tags += "t3"

    assert tags == {"t1", "t2", "t3"}
