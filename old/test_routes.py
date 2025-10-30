# coding: utf-8

import logging
import pytest

from space.router import MethodArgsRouter

log = logging.getLogger(__name__)


def n(ffak_list):
    return sorted(ffak.func.__name__ for ffak in ffak_list)


@pytest.fixture
def mmr(objs):
    return MethodArgsRouter(objs.me, "can_move")


def test_mmr_dir(mmr):
    assert set(mmr.dir) == set(["can_move_words", "can_move_obj_words"])


def test_mmr_kw(a_map, objs, mmr):
    dir_only = mmr.fill(moves=("n",))
    obj_also = mmr.fill(obj=objs.ubi, moves=("n",))

    assert n(dir_only) == ["can_move_words"]
    assert n(obj_also) == ["can_move_obj_words", "can_move_words"]


def test_mmr_pa(a_map, objs, mmr):
    dir_only = mmr.fill(("n",))
    obj_also = mmr.fill(objs.ubi, ("n",))

    assert n(dir_only) == ["can_move_words"]
    assert n(obj_also) == ["can_move_obj_words"]


def test_can_move(objs, mmr):
    ok, ctx = mmr(moves=("n",))
    assert ok is False
    assert "error" in ctx

    # XXX: this should be false. If the door is closed, that ubi is too far
    # away for now, it parses correctly though, cuz the obj is technically on
    # the map somewhere.
    # TODO # ok,ctx =  mmr(obj=objs.ubi, moves=("n",))
    # TODO # assert ok is False
    # TODO # assert 'error' in ctx

    objs.me.do("open door; sSWss")
    assert mmr(moves=("s",)) == (True, {"moves": ("s",)})
    assert mmr(obj=objs.ubi, moves=("n",)) == (True, {"obj": objs.ubi, "moves": ("n",)})


@pytest.fixture
def mor(objs):
    return MethodArgsRouter(objs.me, "can_open")


def test_mor_dir(mor):
    assert set(mor.dir) == set(["can_open_obj"])


def test_mor_kw(objs, mor):
    obj_only = mor.fill(obj=objs.door)

    assert n(obj_only) == ["can_open_obj"]
