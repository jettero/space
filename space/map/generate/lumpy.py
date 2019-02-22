# coding: utf-8

import random
import logging

from ...roll import Roll, roll
from ..cell import Wall, Cell
from ..room import Room

log = logging.getLogger(__name__)

def generate(x=20, y=20, rsz='1d4+1', rooms='3d4', cellify_partitions=True):
    rsz = Roll(rsz)
    m = Room(rsz.roll(), rsz.roll())
    retries = 10
    rooms = roll(rooms)
    while rooms > 0:
        walls = [ x for x in m.iter_locations(Wall) if x.has_neighbor(of_type=Cell) ]
        while True:
            cw = random.choice(walls)
            cx,cy = cw.pos
            r = Room(rsz.roll(), rsz.roll())
            rb = r.bounds
            px = cx if cw.dtype('e', type(None)) else cx - rb.X
            py = cy if cw.dtype('s', type(None)) else cy - rb.Y
            n = m.clone()
            n[px,py] = r
            nb = n.bounds
            if nb.X <= x and nb.Y <= y:
                m = n
                if cellify_partitions:
                    m.cellify_partitions()
                m.strip_useless_walls()
                retries = 10
                log.debug('added %s at (%d,%d)', repr(r), px, py)
                rooms -= 1
                break
            else:
                log.debug('%s is too big to add at (%d,%d) under constraint (%d,%d) retries=%d',
                    repr(r), px, py, x,y, retries)
                retries -= 1
                if retries < 1:
                    return m
    m.condense()
    return m
