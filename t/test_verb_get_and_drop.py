# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

from space.parser import Parser


@pytest.fixture
def me(objs):
    return objs.me


def test_get_and_drop_bauble(me, a_map):
    p = Parser()

    # Open door and walk to the bauble using compound commands and directions
    # Compound commands must go through the shell
    me.do('open door; sSW6s3w')

    # We should now be at or very near the bauble at (4,9)
    assert isinstance(me.location.pos, tuple)

    # pick up the useless bauble (typo in spec: 'buable')
    ps = p.parse(me, 'get buable')
    if not ps:
        # fall back to the correct spelling if parser rejects the typo
        ps = p.parse(me, 'get bauble')
    assert ps and ps.winner.verb.name == 'get'
    ps()

    # ensure it is now in our pack
    assert any(getattr(i, 's', '') == 'bauble' for i in me.pack)

    # move a bit east, then drop it
    p.parse(me, '3e')()
    ps = p.parse(me, 'drop bauble')
    assert ps and ps.winner.verb.name == 'drop'
    ps()

    # verify it's no longer in our pack
    assert not any(getattr(i, 's', '') == 'bauble' for i in me.pack)
