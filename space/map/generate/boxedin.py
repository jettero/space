# coding: utf-8

import logging

from ..cell import Wall

from .rdropper import generate_rooms
#from .base import sparse

log = logging.getLogger(__name__)

def generate(x=50, y=50, rsz='2d4+1', rsparse='1d10+3'):
    a_map = generate_rooms(x=x, y=y, rsz=rsz, rsparse=rsparse)
    a_map.cellify_partitions()

    visited = set()
    for _,wall in a_map.iter_type(Wall):
        if wall in visited:
            continue
        to_see = [ wall ]
        while to_see:
            t = to_see.pop(0)
            visited.add(t)
            for n in t.neighbors():
                if n in visited or not isinstance(n, Wall):
                    continue
                if isinstance(n, Wall):
                    to_see.append(n)

    # plan
    # add corridors until all rooms in {visited} are connected
    # but first, these annoying bugs in cellify_partitions

    #a_map.condense()
    #a_map.strip_useless_walls()
    return a_map
