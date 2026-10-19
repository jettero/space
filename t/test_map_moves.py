# coding: utf-8

from math import dist
from space.map import Wall


def test_path_to_around_wall(a_map, objs):
    dd, me = objs.dig_dug, objs.me
    a_map[6, 7] = dd
    a_map[7, 4] = me
    for x in (5, 6, 7):
        a_map[x, 6] = Wall()
    moves = dd.path_to(me)
    ok, ctx = dd.path_for(dd, moves)
    assert ok and len(moves) == 3
    assert dist(ctx["cells"][-1].pos, me.location.pos) <= dd.reach


def test_move_me_to_ubi(a_map, objs):
    assert a_map[objs.me] is not a_map[objs.ubi]
    a_map[a_map[objs.ubi].pos] = objs.me
    assert a_map[objs.me] is a_map[objs.ubi]


def test_move_ubi_to_me(a_map, objs):
    assert a_map[objs.me] is not a_map[objs.ubi]
    a_map[a_map[objs.me].pos] = objs.ubi
    assert a_map[objs.me] is a_map[objs.ubi]
