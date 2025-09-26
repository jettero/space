# coding: utf-8

import logging
import pytest

from space.router import MethodArgsRouter

log = logging.getLogger(__name__)

def n(ffak_list):
    return sorted(ffak.func.__name__ for ffak in ffak_list)

@pytest.fixture
def mmr(objs):
    return MethodArgsRouter(objs.me, 'can_move', multi=True)

def test_mmr_dir(mmr):
    assert set(mmr.dir) == set(['can_move_words', 'can_move_obj_words'])

def test_mmr_kw(a_map, objs, mmr):
    dir_only = mmr.fill(moves=('n',))
    obj_also = mmr.fill(obj=objs.ubi, moves=('n',))

    assert n(dir_only) == ['can_move_words']
    assert n(obj_also) == ['can_move_obj_words', 'can_move_words']

def test_mmr_pa(a_map, objs, mmr):
    dir_only = mmr.fill(('n',))
    obj_also = mmr.fill(objs.ubi, ('n',))

    assert n(dir_only) == ['can_move_words']
    assert n(obj_also) == ['can_move_obj_words', 'can_move_words']

def test_can_move(a_map, objs, mmr):
    ok, ctx = mmr(moves=('s',))
    assert ok is False
    assert ctx.get('moves') == ('s',)
    assert mmr(moves=('n',)) == (False, {'moves': ('n',)})
    assert mmr(obj=objs.ubi, moves=('n',)) == (True, {'obj': objs.ubi, 'moves': ('n',)})

    # open the south door cell between rooms so moving south is allowed
    a_map[8,2].do_open()
    ok, ctx = mmr(moves=('s',))
    assert ok is True
    assert ctx.get('moves') == ('s',)

@pytest.fixture
def mor(objs):
    return MethodArgsRouter(objs.me, 'can_open', multi=True)

def test_mor_dir(mor):
    assert set(mor.dir) == set(['can_open_obj', 'can_open_word', 'can_open_word_obj'])
