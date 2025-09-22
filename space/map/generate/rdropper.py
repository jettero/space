"""
Room Dropper (core)

Drops rectangular rooms within a bounding map until a sparseness target is
reached. Enforces a minimum gap between rooms (min_gap) to avoid shared walls
or touching corners, then optionally cellifies partitions, strips useless walls,
and condenses the map.

Used by multiple generators (rdc, boxed-in) as the room layout step.
"""
import random
import logging

from ...roll import Roll
from ..base import Map
from ..room import Room
from .base import sparse

log = logging.getLogger(__name__)

def _room_bbox(pos, room):
    bx, by = pos
    rb = room.bounds
    return (bx, by, bx + rb.X, by + rb.Y)

def _boxes_too_close(box1, box2, min_gap=1):
    # Expand box1 by min_gap and check intersection with box2
    x1, y1, X1, Y1 = box1
    x2, y2, X2, Y2 = box2
    x1 -= min_gap; y1 -= min_gap; X1 += min_gap; Y1 += min_gap
    # Check overlap
    return not (X1 < x2 or X2 < x1 or Y1 < y2 or Y2 < y1)

def generate_rooms(x=50, y=50, rsz='2d4+2', rsparse='1d10+3', cellify_partitions=True, min_gap=1):
    rsparse = sparse(rsparse)
    rsz = Roll(rsz)
    a_map = Map(x,y)
    s = 1.0
    placed_boxes = []
    while s > rsparse:
        r = Room(rsz.roll(), rsz.roll())
        ab = a_map.bounds
        rb = r.bounds
        xr = ab.X-(rb.X-1)
        yr = ab.Y-(rb.Y-1)
        if xr > 0 and yr > 0:
            # attempt a few times to place with min_gap
            for _ in range(20):
                px = random.randint(0, ab.X-rb.X)
                py = random.randint(0, ab.Y-rb.Y)
                bb = _room_bbox((px, py), r)
                if any(_boxes_too_close(bb, ob, min_gap=min_gap) for ob in placed_boxes):
                    continue
                log.debug('[%0.2f < %0.2f] placing %s at %d,%d', rsparse, s, repr(r), px,py)
                a_map[px,py] = r
                placed_boxes.append(bb)
                s = a_map.sparseness
                break
        else:
            log.debug("[%0.2f < %0.2f] %s won't fit in %s", rsparse, s, repr(r), repr(a_map))
    if cellify_partitions:
        a_map.cellify_partitions()
    a_map.strip_useless_walls()
    a_map.condense()
    return a_map
