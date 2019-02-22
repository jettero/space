# coding: utf-8

import random
import logging

from ...roll import Roll
from ..base import Map
from ..room import Room
from .base import sparse

log = logging.getLogger(__name__)

def generate_rooms(x=50, y=50, rsz='2d4+2', rsparse='1d10+3', cellify_partitions=True):
    rsparse = sparse(rsparse)
    rsz = Roll(rsz)
    a_map = Map(x,y)
    s = 1.0
    while s > rsparse:
        r = Room(rsz.roll(), rsz.roll())
        ab = a_map.bounds
        rb = r.bounds
        xr = ab.X-(rb.X-1)
        yr = ab.Y-(rb.Y-1)
        if xr > 0 and yr > 0:
            x = random.randint(0, ab.X-rb.X)
            y = random.randint(0, ab.Y-rb.Y)
            log.debug('[%0.2f < %0.2f] placing %s at %d,%d', rsparse, s, repr(r), x,y)
            a_map[x,y] = r
            s = a_map.sparseness
        else:
            log.debug("[%0.2f < %0.2f] %s won't fit in %s", rsparse, s, repr(r), repr(a_map))
    if cellify_partitions:
        a_map.cellify_partitions()
    a_map.strip_useless_walls()
    a_map.condense()
    return a_map
