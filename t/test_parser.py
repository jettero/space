# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import logging
import pytest

from space.living    import Human
from space.parser    import Parser
from space.map       import Room

import space.exceptions as E

log = logging.getLogger(__name__)

@pytest.fixture
def people():
    return ( Human('John Snow'), Human('Jaime Lannister'), Human('Jorah Mormont') )

@pytest.fixture
def room(people):
    r = Room()
    for i,p in enumerate(people):
        r[2+i,3].add_item(p)
    return r

@pytest.fixture
def me(people):
    return people[0]

@pytest.fixture
def target(people):
    return people[1]

@pytest.fixture
def bystander(people):
    return people[2]

def test_attack_parse(me, target, room):
    p = Parser()
    pstate = p.parse(me, 'attack jaime')
    assert pstate.winner.verb.name == 'attack'
    assert pstate.winner.do_args.get('target') == target

def test_attack_exec(me, target, room):
    p = Parser()
    hp1 = target.hp
    p.parse(me, 'attack jaime')()
    hp2 = target.hp
    assert hp2 < hp1

def test_move_parse(me, room):
    p = Parser()
    dt = {
        'n': 'north North NORTH nOrth n'.split(),
        's': 'south South s'.split(),
        'e': 'east East e'.split(),
        'w': 'west West w'.split(),
    }
    room[7,7] = me
    for d,sl in dt.items():
        for s in sl:
            pstate = p.parse(me, f'move {s}')
            assert bool(pstate)
            assert pstate.winner.do_args.get('moves') == (d,)
            assert pstate.winner.verb.name == 'move'

def test_move(me, target, room):
    p = Parser()
    assert me.location.pos == (2,3)
    p.parse(me, 'move north')()
    assert me.location.pos == (2,2)
    p.parse(me, 'move east')()
    assert me.location.pos == (3,2)
    pstate = p.parse(me, 'move s')
    assert 'is already there' in str(pstate.error)
    with pytest.raises(E.ContainerError):
        pstate()
    assert me.location.pos == (3,2)

def test_naked_dir_move_cmds(me, bystander, room):
    p = Parser()
    pstate = p.parse(me, 'move 2sse')
    tsse = ('s','s','s','e')
    assert pstate
    assert pstate.high_score_verb.name == 'move'
    assert pstate.high_score_args.get('moves') == tsse

    pstate = p.parse(me, 'move shit')
    assert not pstate
    assert pstate.high_score_verb.name == 'move'
    assert pstate.high_score_args == None

    pstate = p.parse(me, '2sse')
    assert pstate
    assert pstate.high_score_verb.name == 'move'
    assert pstate.high_score_args.get('moves') == tsse

    tssep = tsse + ('n','s','e','w')
    pstate = p.parse(me, 'move 2sse nsew')
    assert pstate.high_score_verb.name == 'move'
    assert pstate.high_score_args.get('moves') == tssep

    pstate = p.parse(me, '2sse nsew')
    assert pstate.high_score_verb.name == 'move'
    assert pstate.high_score_args.get('moves') == tssep


def test_irritating_psnode_issue(me, room):
    p = Parser()
    pstate = p.parse(me, '')
    assert pstate.states
    for psn in pstate.states:
        if psn.fname:
            assert psn.verb.name in psn.fname
