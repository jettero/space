# coding: utf-8

import random
import logging

from ..cell import Cell, Wall
from ..dir_util import translate_dir

from .base import sparse
from .rdropper import generate_rooms

log = logging.getLogger(__name__)

def select_wall(a_map):
    def _useful(a_cell):
        for d in 'nsew':
            if a_cell.dtype(d, Cell):
                o = a_cell.r_dpos(d)
                if a_map.in_bounds(*o):
                    return True
    walls = list([ a_cell for pos,a_cell in a_map.iter_type(Wall) if _useful(a_cell) ])
    return random.choice(walls)

def add_corridor(a_map, csparse='1d8+3', dir_bias=6):
    s = a_map.sparseness
    csparse = sparse(csparse, start=s)
    visited = set()

    pos = select_wall(a_map).pos
    a_cell = Cell(mobj=a_map, pos=pos)
    a_map[pos] = a_cell
    visited.add(pos)
    log.debug('[%0.2f < %0.2f] placed %s at %s', csparse, s, a_cell, pos)

    nonetype = type(None)
    ld = d = None
    b = a_map.bounds
    def lok(q): # pylint: disable=invalid-name
        return not( q[0]<=0 or q[1]<=0 or q[0]>=b[2] or q[1]>=b[3] )

    while s > csparse:
        if d is not None and ld != d:
            dc = [ (d,translate_dir(d,pos)) ]
        else:
            dc = [ (x,translate_dir(x,pos)) for x in 'nsew' if a_cell.dtype(x, nonetype) ]
        dc = [ x for x,q in dc if q not in visited and lok(q) ]
        if not dc:
            break
        if d in dc and dir_bias > 1:
            dc += [d] * (dir_bias-1)
        ld = d
        d = random.choice(dc)
        pos = translate_dir(d, pos)
        a_cell = Cell(mobj=a_map, pos=pos)
        a_map[pos] = a_cell
        visited.add(pos)

        log.debug('[%0.2f < %0.2f] placed %s at %s', csparse, s, a_cell, pos)
        s = a_map.sparseness

    for pos in visited:
        for d in ['n','s','e','w', 'ne','se','nw','sw']:
            if a_map[pos].dtype(d, nonetype):
                a_map[translate_dir(d,pos)] = Wall(mobj=a_map, pos=pos)

def generate(x=50, y=50, rsz='2d4+1', rsparse='1d10+3', asparse='1d8+2', csparse='1d8+3', dir_bias=6):
    a_map = generate_rooms(x=x, y=y, rsz=rsz, rsparse=rsparse)
    s = a_map.sparseness
    asparse = sparse(asparse, start=s)
    while s > asparse:
        add_corridor(a_map, csparse=csparse, dir_bias=dir_bias)
        s = a_map.sparseness
    a_map.condense()
    a_map.strip_useless_walls()
    return a_map
