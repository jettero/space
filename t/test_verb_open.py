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
    # For now, we only assert parse intent; execution may fail later
    assert pstate
    assert pstate.winner.verb.name == 'open'

def test_open_parse_targets_directional_north_fails(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open north door')
    # No door to the north in this map; parsing should fail
    assert not pstate
    with pytest.raises(E.ParseError):
        pstate()


def test_open_exec_closed_door_blocks_then_allows_move(me, a_map):
    p = Parser()

    # First, moving south should fail because door is closed
    pstate = p.parse(me, 'move south')
    assert pstate and pstate.winner.verb.name == 'move'
    with pytest.raises(E.ParseError):
        pstate()

    # Opening the door should succeed (no exception on call)
    p_open = p.parse(me, 'open door')
    assert p_open and p_open.winner.verb.name == 'open'
    p_open()  # do not assert effects beyond no exception; implementation TBD

    # After opening, moving south should now succeed
    p_move = p.parse(me, 'move south')
    assert p_move and p_move.winner.verb.name == 'move'
    p_move()
    # In t/troom.py, the me starts at (8,1) and the closed door is at (8,2)
    assert me.location.pos == (8, 2)


def test_open_wrong_target_fails(me, a_map):
    p = Parser()
    pstate = p.parse(me, 'open nothingburger')
    # Expect parse to not find a valid target/action
    assert not pstate
    # Executing should raise since no valid winner
    with pytest.raises(E.ParseError):
        pstate()
