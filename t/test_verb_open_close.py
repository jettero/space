# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

from space.parser import Parser

import space.exceptions as E


@pytest.fixture
def me(objs):
    return objs.me


def test_open_door(me, a_map):
    p = Parser()
    pstate = p.parse(me, "open door")
    assert pstate
    assert pstate.winner.verb.name == "open"


# def test_open_south_door(me, a_map):
#     p = Parser()
#     pstate = p.parse(me, 'open south door')
#     assert pstate
#     assert pstate.winner.verb.name == 'open'

# def test_open_north_door_fail(me, a_map):
#     p = Parser()
#     pstate = p.parse(me, 'open north door')
#     assert not pstate
#     with pytest.raises(E.ParseError, match=r"north|no .*door|can't|cannot|invalid|not.*exist"):
#         pstate()

# def test_open_nonsense_fails(me, a_map):
#     p = Parser()
#     pstate = p.parse(me, 'open nothingburger')
#     assert not pstate
#     with pytest.raises(E.ParseError, match=r"nothingburger|no .*target|unknown|not .*found|invalid"):
#         pstate()

# def test_open_nonsense_door_fails(me, a_map):
#     p = Parser()
#     pstate = p.parse(me, 'open nothingburger door')
#     assert not pstate
#     with pytest.raises(E.ParseError, match=r"nothingburger|no .*target|unknown|not .*found|invalid"):
#         pstate()

# def test_open_door_and_move_through_it(me, a_map):
#     p = Parser()

#     pstate = p.parse(me, 'move south')
#     assert not pstate
#     assert pstate.winner is None
#     assert 'door is closed' in pstate.error
#     with pytest.raises(E.ParseError, match=r"door is closed"):
#         pstate()

#     p_open = p.parse(me, 'open door')
#     assert p_open and p_open.winner.verb.name == 'open'
#     p_open()

#     p_move = p.parse(me, 'move south')
#     assert p_move and p_move.winner.verb.name == 'move'
#     p_move()
#     assert me.location.pos == (8, 2)
