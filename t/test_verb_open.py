# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import pytest

from space.parser import Parser

import space.exceptions as E


@pytest.fixture
def me(objs):
    return objs.me


def test_open_parse_targets_door(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open door')
    assert pstate
    assert pstate.winner.verb.name == 'open'

def test_open_parse_targets_directional_south(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open south door')
    assert pstate
    assert pstate.winner.verb.name == 'open'

def test_open_parse_targets_directional_north_fails(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open north door')
    assert not pstate
    with pytest.raises(E.ParseError) as excinfo:
        pstate()

def test_open_exec_closed_door_blocks_then_allows_move(me, a_map):
    p = Parser()

    pstate = p.parse(me, 'move south')
    assert not pstate
    assert pstate.winner is None
    assert 'door is closed' in pstate.error
    with pytest.raises(E.ParseError, match=r"door is closed"):
        pstate()

    p_open = p.parse(me, 'open door')
    assert p_open and p_open.winner.verb.name == 'open'
    p_open()

    p_move = p.parse(me, 'move south')
    assert p_move and p_move.winner.verb.name == 'move'
    p_move()
    assert me.location.pos == (8, 2)


def test_open_wrong_target_fails(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open nothingburger')
    assert not pstate
    with pytest.raises(E.ParseError):
        pstate()
