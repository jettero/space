# coding: utf-8
# pylint: disable=invalid-name

__all__ = ['a_map', 'o']

def gen_troom():
    from space.map.room import Room
    from space.living import Human
    from space.item import Ubi
    from space.nico import nico

    a_map = Room(4,4)
    a_map[3,2] = Room(5,7)
    a_map[7,0] = Room(3,4)
    a_map.cellify_partitions()

    od = dict()
    a_map[8,1] = od['me']      = Human('Paul Miller', 'Paul')
    a_map[4,9] = od['ubi']     = Ubi()
    a_map[1,2] = od['stupid']  = Human('Stupid Rapist')
    a_map[8,3] = od['dig_dug'] = Human('Dig Dug')
    o = nico(**od)

    o.me.active = True

    return a_map, o

a_map, o = gen_troom()
