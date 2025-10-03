# coding: utf-8
# pylint: disable=invalid-name

__all__ = ["e_map", "o"]


def gen_eroom():
    from space.map import Room
    from space.nico import nico
    from space.living import Human

    e_map = Room(20, 20)
    od = dict()
    e_map[9, 9] = od["me"] = Human("Paul Miller", "Paul")
    o = nico(**od)
    o.me.active = True

    return e_map, o


e_map, o = gen_eroom()
