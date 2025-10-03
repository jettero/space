# coding: utf-8


def test_move_me_to_ubi(a_map, objs):
    assert a_map[objs.me] is not a_map[objs.ubi]
    a_map[a_map[objs.ubi].pos] = objs.me
    assert a_map[objs.me] is a_map[objs.ubi]


def test_move_ubi_to_me(a_map, objs):
    assert a_map[objs.me] is not a_map[objs.ubi]
    a_map[a_map[objs.me].pos] = objs.ubi
    assert a_map[objs.me] is a_map[objs.ubi]
