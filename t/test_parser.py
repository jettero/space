# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import logging
import pytest

from space.living    import Human
from space.parser    import Parser
from space.map       import Room
from space.container import ContainerError

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
    verb, kw = p.parse(me, 'attack jaime', verb_exec=False)
    assert verb.name == 'attack'
    assert kw['target'] == target

def test_attack_exec(me, target, room):
    p = Parser()
    hp1 = target.hp
    p.parse(me, 'attack jaime')
    hp2 = target.hp
    assert hp2 < hp1

@pytest.mark.xfail(strict=True)
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
            try:
                verb, kw = p.parse(me, f'move {s}', verb_exec=False)
            except SyntaxError as e:
                verb, kw = None, {'error': str(e)}
            assert 'moves' in kw and kw['moves'] == (d,)
            assert verb and verb.name == 'move'

def test_move(me, target, room):
    p = Parser()
    assert me.location.pos == (2,3)
    p.parse(me, 'move north')
    assert me.location.pos == (2,2)
    p.parse(me, 'move east')
    assert me.location.pos == (3,2)
    with pytest.raises(ContainerError) as ce:
        p.parse(me, 'move south')
    assert f'{target}' in str(ce)
    assert me.location.pos == (3,2)

def test_naked_dir_move_cmds(me, bystander, room):
    p = Parser()
    verb, kw = p.parse(me, 'move 2sse', False,False)
    assert verb.name == 'move'
    assert kw['words'] == '2sse'

    verb, kw = p.parse(me, 'move shit', False,False)
    assert verb.name == 'move'
    assert kw['words'] == 'shit'

    verb, kw = p.parse(me, '2sse', False, False)
    assert verb.name == 'move'
    assert kw['words'] == '2sse'

    with pytest.raises(SyntaxError):
        verb, kw = p.parse(me, 'shit', False, False)

    verb, kw = p.parse(me, 'move 2sse nsew', False,False)
    assert verb.name == 'move'
    assert kw['words'] == '2sse nsew'

    verb, kw = p.parse(me, '2sse nsew', False,False)
    assert verb.name == 'move'
    assert kw['words'] == '2sse nsew'
