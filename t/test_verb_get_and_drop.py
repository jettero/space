# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

from space.item import Chair
from space.living import Quadruped


@pytest.fixture
def me(objs):
    return objs.me


def test_get_and_drop_bauble(me):
    # Open door and walk to the bauble using compound commands and directions
    # Compound commands must go through the shell
    me.do("open door; sSW6s3w")
    me.do("look")

    # We should now be at or very near the bauble at (4,9)
    assert me.location.pos, (4, 9)

    # pick up the useless bauble (typo in spec: 'bauble')
    xp = me.parse("get bauble")
    assert xp
    assert xp.fn.__name__ == "do_get_obj"
    xp()

    # ensure it is now carried in hands
    # Slot properties expose the item directly (or None)
    held = [i for i in (me.slots.left_hand, me.slots.right_hand) if i is not None]
    names = [i.s for i in held]
    assert "bauble" in names

    me.do("3e")

    me.do("drop bauble")

    # verify it's no longer carried in hands (ignore pack)
    held = [i for i in (me.slots.left_hand, me.slots.right_hand) if i is not None]
    names = [i.s for i in held]
    assert "bauble" not in names


@pytest.fixture
def dog(objs, a_map):
    a_map[4, 8] = q = Quadruped()
    return q


def test_quadruped_get_and_drop(dog, objs):
    assert (xp := dog.parse("get bauble")), xp.error
    xp()
    assert dog.slots.mouth is objs.ubi
    assert (xp := dog.parse("drop bauble")), xp.error
    xp()
    assert objs.ubi.location is dog.location


def test_quadruped_mouth_full(dog, a_map):
    dog.do("get bauble")
    a_map[5, 8] = Chair()
    assert not (xp := dog.parse("get chair"))
    assert "not possible" in str(xp.error)
