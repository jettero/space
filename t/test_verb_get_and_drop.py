# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest


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
