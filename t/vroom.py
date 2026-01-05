# coding: utf-8
# pylint: disable=invalid-name

__all__ = ["v_map", "o"]

# This is pretty much the troom, but without a door, less shit on the floor and
# frozen in time so we don't have to change the visicalc tests when troom
# changes.


def gen_vroom():
    from space.map import Room, BlockedCell, Wall
    from space.living import Human
    from space.nico import nico

    a_map = Room(4, 4)
    a_map[3, 2] = Room(5, 7)
    a_map[7, 0] = Room(3, 4)
    a_map.cellify_partitions()

    a_map[8, 2] = bc = BlockedCell()
    a_map[9, 2] = Wall()
    a_map[9, 1] = Wall()

    od = {"door": bc.door}
    a_map[8, 1] = od["me"] = Human("Paul Miller", "Paul", gender="male")
    o = nico(**od)

    o.me.active = True

    return a_map, o


v_map, o = gen_vroom()
