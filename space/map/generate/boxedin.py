"""
Boxed-in Rooms Generator

Lays out rooms via rdropper.generate_rooms, then carves corridors from room
edges using a biased random walk until a target sparseness is reached.

Useful for compact room clusters with connecting hallways. For finer control
over straightness/loops/pruning, prefer rdc.generate.
"""

import logging
import random

from ..cell import Wall, Cell, Corridor

from .rdropper import generate_rooms

# from .base import sparse

log = logging.getLogger(__name__)


def generate(x=50, y=50, rsz="2d4+1", rsparse="1d10+3"):
    """Generate boxed-in rooms with corridors.

    Uses rdropper to place rooms, cellifies short partitions, then carves
    corridors and reconstructs walls.
    """
    a_map = generate_rooms(x=x, y=y, rsz=rsz, rsparse=rsparse)
    a_map.cellify_partitions()

    visited = set()
    for _, wall in a_map.iter_type(Wall):
        if wall in visited:
            continue
        to_see = [wall]
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

    # Open doors along corridors with a bias, then reconstruct walls
    open_doors_along_corridors(a_map, prob=0.6, max_doors_per_room=2)
    reconstruct_walls(a_map)
    # Add doors where corridors meet rooms
    a_map.place_doors()
    a_map.condense()
    a_map.strip_useless_walls()
    return a_map


def reconstruct_walls(a_map):
    nonetype = type(None)
    to_wall = []
    for (i, j), c in a_map:
        if isinstance(c, Cell):
            for dd, (dx, dy) in {
                "n": (0, -1),
                "s": (0, 1),
                "e": (1, 0),
                "w": (-1, 0),
                "ne": (1, -1),
                "nw": (-1, -1),
                "se": (1, 1),
                "sw": (-1, 1),
            }.items():
                p = (i + dx, j + dy)
                if not a_map.in_bounds(*p):
                    continue
                q = a_map[p]
                if isinstance(q, nonetype):
                    to_wall.append(p)
    for p in to_wall:
        a_map[p] = Wall(mobj=a_map, pos=p)


def open_doors_along_corridors(a_map, prob=0.6, max_doors_per_room=2):
    opened = {}
    for (i, j), w in a_map:
        if not isinstance(w, Wall):
            continue
        for d, (dx, dy) in {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0)}.items():
            p1 = (i + dx, j + dy)
            p2 = (i - dx, j - dy)
            if not (a_map.in_bounds(*p1) and a_map.in_bounds(*p2)):
                continue
            c1 = a_map[p1]
            c2 = a_map[p2]
            # open only when one side is room-interior Cell and the other is corridor Cell
            if isinstance(c1, Cell) and isinstance(c2, Cell):
                cnt = opened.get(p1, 0) + opened.get(p2, 0)
                if cnt >= max_doors_per_room:
                    continue
                if random.random() <= prob:
                    a_map[i, j] = Corridor(mobj=a_map, pos=(i, j))
                    opened[p1] = opened.get(p1, 0) + 1
                    opened[p2] = opened.get(p2, 0) + 1
                    break
