# coding: utf-8

import heapq
import logging
import math
import random
from collections import namedtuple
from functools import lru_cache

from ..obj import baseobj
from ..container import Containable, Container
from .cell import Cell, Floor, Corridor, MapObj, Wall
from .cell.blocked import BlockedCell
from .dir_util import convert_pos, DIRS, DDIRS
from .util import LineSeg, Box, Bounds, test_maxdist
from ..time import Time

import space.exceptions as E

log = logging.getLogger(__name__)

SHADOW = 10


class Map(baseobj):
    whom = None
    seen = frozenset()

    @classmethod
    def atosz(cls, a):
        if len(a) >= 2:
            return a[0:2]
        if len(a) == 1:
            return a[0], a[0]
        return 10, 10

    def __init__(self, *a):
        x, y = self.atosz(a)
        self.cells = []
        self.time = Time(self)
        self.set_min_size(x, y)
        self.invalidate()

    @property
    def bounds(self):
        return Bounds(self.cells)

    def __repr__(self):
        return f"{self.cname}({self.bounds})#{self.id}"

    def __str__(self):
        if not self.cells:
            return ""
        r = ["   " + "".join([str(i % 10) for i, _ in enumerate(self.cells[0])])] + [
            f"{i:2} " + l for i, l in enumerate(self.text_drawing(color=True).splitlines())
        ]
        return "\n".join(r)

    def clear_tags(self):
        for p, c in self.iter_type():
            c.tags.clear()

    def unobstructed_distance(self, obj1, obj2):
        """assuming there are no obstructions at all, compute the distance between two objects"""
        c1 = self.find_obj(obj1)
        c2 = self.find_obj(obj2)
        if c1 and c2:
            return LineSeg(c1, c2).distance

    @property
    def objects(self):
        for row in self.cells:
            for cell in row:
                if isinstance(cell, Container):
                    yield from cell

    def objects_of_type(self, of_type):
        for obj in self.objects:
            if isinstance(obj, of_type):
                yield obj

    def find_obj(self, obj):
        if isinstance(obj, MapObj):
            return obj.pos
        # NOTE: we don't use obj.location because it may not be defined yet
        # or it may come to be incorrect during certain assignment operations
        for row in self.cells:
            for cell in row:
                if isinstance(cell, Container) and obj in cell:
                    return cell

    def _text_drawing(self, viewer=None, cell_join=None, lines_join=None):
        lines = list()
        here = viewer.location if viewer is not None else None

        for row in self.cells:
            line = [" " if c is None else "@" if c is here else c.abbr for c in row]
            if cell_join is not None:
                line = cell_join.join(line)
            lines.append(line)
        if lines_join is not None:
            return lines_join.join(lines)
        return lines

    def text_drawing(self, viewer=None, color=False) -> str:
        """
        The cells as text, one line per row, drawn for `viewer` -- who
        sees themself as "@".  Nobody is looking when viewer is None, so
        every living draws as its own glyph.

        With color, each cell also carries an ANSI prefix: dim for walls
        and plain floor, brown for doors, and a background wash on
        anything in self.seen.
        """

        if not color:
            return self._text_drawing(viewer, cell_join="", lines_join="\n")

        text_drawing = self._text_drawing(viewer)

        last_color = ""
        boring_color = {"fg": 240}
        door_color = {"fg": 130}  # brown/dark orange
        neutral_color = {"fg": 254}
        can_see_color = {"bg": 17}
        rst = "\x1b[m"

        def _assign_color(i, j, bg=None, fg=None):  # pylint: disable=invalid-name
            color = rst
            if bg is not None:
                color += f"\x1b[48;5;{bg}m"
            if fg is not None:
                color += f"\x1b[38;5;{fg}m"
            if color != last_color:
                text_drawing[j][i] = color + text_drawing[j][i]
            return color

        for j, row in enumerate(self.cells):
            for i, cell in enumerate(row):
                if cell is None:
                    last_color = _assign_color(i, j)
                    continue
                color = dict()
                if isinstance(cell, BlockedCell) and cell.has_door:
                    color.update(door_color)
                else:
                    color.update(boring_color if isinstance(cell, Wall) or cell.abbr == "." else neutral_color)
                if cell.pos in self.seen:
                    color.update(can_see_color)
                last_color = _assign_color(i, j, **color)
            text_drawing[j] += rst
            last_color = ""

        return "\n".join(["".join(x) for x in text_drawing])

    def _set_min_rows(self, y):
        while len(self.cells) < y:
            self.cells.append(list())

    def _set_min_cols(self, x):
        x = max([x] + [len(r) for r in self.cells])
        for row in self.cells:
            d = x - len(row)
            if d > 0:
                row += [None] * d

    def set_min_size(self, x, y):
        self._set_min_rows(y)
        self._set_min_cols(x)

    def in_bounds(self, *a):
        return self.bounds.contains(*a)

    def get(self, x, y):
        if not self.in_bounds(x, y):
            return
        return self.cells[y][x]

    def __getitem__(self, pos):
        if isinstance(pos, (MapObj, Containable)):
            return self.find_obj(pos)
        pos = convert_pos(pos)
        return self.get(*pos)

    def drop_item_randomly(self, item, retries=10):
        if not isinstance(item, Containable):
            raise ValueError(f"only containable items can be randomly dropped")
        while retries > 0:
            c = self.random_location()
            try:
                c.add_item(item)
                return
            except E.ContainerError:  # thing is already there
                pass
            retries -= 1
        raise ValueError(f"not sure how to insert {item}")

    def __setitem__(self, pos, item):
        if pos in (None, "-", "rand", "random", "?"):
            return self.drop_item_randomly(item)
        pos = convert_pos(pos)
        if isinstance(item, Map):
            pos = self._translate_map(*pos)
            return self.insert_map(*pos, item)
        if item is None or isinstance(item, MapObj):
            pos = self._translate_map(*pos)
            return self.insert_mapobj(*pos, item)
        if isinstance(item, Containable):
            c = self.get(*pos)
            if isinstance(c, Container):
                return c.add_item(item)
            raise ValueError(f"{item} cannot be placed at {pos} (non-cell location)")
        raise ValueError(f"not sure how to insert {item}")

    def _translate_map(self, x, y):
        sx = 0 if x >= 0 else abs(x)
        sy = 0 if y >= 0 else abs(y)
        x = x if x >= 0 else 0
        y = y if y >= 0 else 0
        if sx or sy:
            for _ in range(sy):
                self.cells.insert(0, [None] * len(self.cells[0]))
            for _ in range(sx):
                for row in self.cells:
                    row.insert(0, None)
        for row in self.cells:
            for cell in row:
                if cell is not None:
                    p = cell.pos
                    cell.pos = (p[0] + sx, p[1] + sy)
        return x, y

    def insert_mapobj(self, x, y, mapobj):
        if mapobj is not None and not isinstance(mapobj, MapObj):
            raise TypeError(f"{repr(self)}.insert_mapobj(pos=({x},{y}), mapobj={mapobj}): " "mapobj is not a MapObj (or None)")

        self.set_min_size(x + 1, y + 1)
        self.cells[y][x] = mapobj
        if mapobj is not None:
            mapobj.pos = (x, y)
            mapobj.map = self
        self.invalidate()

    def insert_map(self, x, y, submap):
        if not isinstance(submap, Map):
            raise TypeError(f"argument: {submap} is not a Map")
        for sj, row in enumerate(submap.cells):
            for si, cell in enumerate(row):
                if cell is None:
                    # NOTE: It's tempting to add a param here
                    # that allows us to insert none ... merge_mode=??
                    # But if we do that, for whatever reason, we'd have to also
                    # go back and repair walls that are crushed during the insert of the None-s.
                    #
                    # This is what happens without `if cell is None: continue`:
                    # In [9]: from space.map.room import Room
                    #    ...: m0 = Room(3,3)
                    #    ...: m1 = Room(3,3)
                    #    ...: m1[4,3] = Room(3,3)
                    #    ...: m0[0,-5] = m1
                    #    ...: %page -r m0
                    #  ┌───────────┐
                    #  │  .  .  .  │
                    #  │  .  .  .  │
                    #  │  .  .  .  ├───────────┐
                    #  └───────────┤  .  .  .  │
                    #              │  .  .  .  │
                    #              │  .  .  .  │
                    #              ├───────────┘
                    #  ╷  .  .  .  │
                    #  └───────────┘
                    continue
                self.insert_mapobj(x + si, y + sj, cell.clone())

    def iter_cells(self, of_type=Cell):
        for _, c in self.iter_type(of_type=of_type):
            yield c

    def random_location(self, of_type=Cell):
        # when we have doors, we should add those iff the door is open
        return random.choice(list(self.iter_cells(of_type=of_type)))

    def randomly_drop(self, obj, retries=20):
        for _ in range(retries):
            try:
                return self.random_location().add_item(obj)
            except ContainerError:
                pass

    def __iter__(self):
        for j, row in enumerate(self.cells):
            for i, cell in enumerate(row):
                yield (i, j), cell

    def iter_type(self, of_type=Cell):
        for p, cell in self:
            if isinstance(cell, of_type):
                yield p, cell

    def strip_useless_walls(self):
        c = 0
        for p, cell in self.iter_type(Wall):
            if cell.useless:
                self[p] = None
                c += 1
        if c > 0:
            log.debug("stripped useless wals c=%d", c)

    def identify_partitions(self, wmin=1, wmax=None):
        partitions = set()
        for check_dir in sorted(DIRS, key=lambda x: random.random()):  # iterate n,s,e,w
            for _, w in self.iter_type(Wall):  # iterate all walls in map
                if w in partitions:
                    continue
                if w.r_dtype(check_dir, Cell):
                    wl = [w]
                    while wl[-1].dtype(check_dir, Wall) and not wl[-1].od_dtype(check_dir, type(None)):
                        wl.append(wl[-1].mpos(check_dir))
                    if len(wl) >= wmin and (wmax is None or len(wl) <= wmax):
                        if wl and wl[-1].dtype(check_dir, Cell):
                            partitions.update(wl)
        return partitions

    def cellify_partitions(self, wmin=1, wmax=None, laps=2):
        """Convert partition walls into floor cells.

        Replaces contiguous runs of walls that partition open areas with
        `Corridor` tiles, effectively opening short passages/doorways.

        Args:
            wmin: Minimum qualifying wall-run length.
            wmax: Optional maximum wall-run length.
            laps: Repeat passes to catch newly exposed partitions.
        """
        for _ in range(laps):
            for wall in self.identify_partitions(wmin=wmin, wmax=wmax):
                # Decide Floor vs Corridor based on immediate neighbors:
                # If all 4 cardinal neighbors are None/Wall/Floor, treat as room smoothing -> Floor
                # Otherwise (touches any non-Floor Cell), treat as corridor opening -> Corridor
                from .cell import Floor, Corridor

                i, j = wall.pos
                neighbors = [(i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)]
                ok_room = True
                for p in neighbors:
                    c = self[p] if self.in_bounds(*p) else None
                    if not (c is None or isinstance(c, Wall) or isinstance(c, Floor)):
                        ok_room = False
                        break
                self[wall.pos] = Floor() if ok_room else Corridor()

    def place_doors(self):
        for (i, j), cell in self:
            if not isinstance(cell, Cell):
                continue
            n = self[i, j - 1] if self.in_bounds(i, j - 1) else None
            s = self[i, j + 1] if self.in_bounds(i, j + 1) else None
            e = self[i + 1, j] if self.in_bounds(i + 1, j) else None
            w = self[i - 1, j] if self.in_bounds(i - 1, j) else None

            def is_wall(x):
                return isinstance(x, Wall)

            def is_floor(x):
                return isinstance(x, Floor)

            def is_corr(x):
                return isinstance(x, Corridor)

            # Vertical doorway: corridor west/east, floor other side; walls north/south
            if is_wall(n) and is_wall(s):
                if (is_corr(w) and is_floor(e)) or (is_floor(w) and is_corr(e)):
                    self[i, j] = BlockedCell()
                    continue

            # Horizontal doorway: corridor north/south, floor other side; walls east/west
            if is_wall(w) and is_wall(e):
                if (is_corr(n) and is_floor(s)) or (is_floor(n) and is_corr(s)):
                    self[i, j] = BlockedCell()
                    continue

    @property
    def sparseness(self):
        none_count = 0
        count = 0
        for _, cell in self:
            count += 1
            if not isinstance(cell, Cell):
                none_count += 1
        return none_count / count

    def clone(self):
        r = self.__class__()
        for p, c in self:
            if c is not None:
                c = c.clone()
            r[p] = c
        return r

    def _e_nj_bound(self):
        rj = None
        for j in range(0, len(self.cells)):
            for c in self.cells[j]:
                if c is not None:
                    return rj
            rj = j

    def _e_sj_bound(self):
        rj = None
        for j in range(len(self.cells) - 1, -1, -1):
            for c in self.cells[j]:
                if c is not None:
                    return rj
            rj = j

    def _e_wi_bound(self):
        ri = None
        for i in range(0, len(self.cells[0])):
            for c in [row[i] for row in self.cells]:
                if c is not None:
                    return ri
            ri = i

    def _e_ei_bound(self):
        ri = None
        for i in range(len(self.cells[0]) - 1, -1, -1):
            for c in [row[i] for row in self.cells]:
                if c is not None:
                    return ri
            ri = i

    def e_bounds(self):
        return [self._e_nj_bound(), self._e_sj_bound(), self._e_ei_bound(), self._e_wi_bound()]

    def condense(self):
        nb, sb, eb, wb = self.e_bounds()
        if sb is not None:
            log.debug("[condense] adjusting s-bound=%d", sb)
            self.cells = self.cells[:sb]
        if nb is not None:
            log.debug("[condense] adjusting n-bound=%d", nb)
            self.cells = self.cells[nb + 1 :]
        if eb is not None:
            log.debug("[condense] adjusting e-bound=%d", eb)
            for j, row in enumerate(self.cells):
                self.cells[j] = row[:eb]
        if wb is not None:
            log.debug("[condense] adjusting w-bound=%d", wb)
            for j, row in enumerate(self.cells):
                self.cells[j] = row[wb + 1 :]
        if nb is not None or wb is not None:
            log.debug("[condense] repositioning cells")
            for p, c in self:
                if c is not None:
                    c.pos = p

    def __eq__(self, other_map):
        if not isinstance(other_map, Map):
            return False
        for p, c in self:
            if type(c) is not type(other_map[p]):
                return False
        return True

    __hash__ = object.__hash__

    def identify_cliques(self):
        cliques = list()

        def find_clique(cell):
            for clique in cliques:
                if cell in clique:
                    return clique

        for cell in self.iter_cells():
            cq = find_clique(cell)
            if cq is None:
                todo = [cell]
                cq = MapClique(todo)
                cliques.append(cq)
                while todo:
                    for n in todo.pop(0).neighbors(of_type=Cell):
                        if n not in cq:
                            cq.add(n)
                            todo.append(n)
        return cliques

    def uberfast_voxel(self, pos1, pos2, ok_type=None, bad_type=None):
        """
        return positions mapped by Fast Voxel: Amanatides, Woo (optimized, no object allocation)

        This should be an exact duplicate of fast_voxel which uses abstractions
        like VV/Box/LineSeg for readability, but which abstractions slow the
        algorithm down horrifically.
        """
        x1, y1 = pos1[0], pos1[1]
        x2, y2 = pos2[0], pos2[1]
        if x1 == x2 and y1 == y2:
            raise ValueError(f"direction undefined for {pos1} == {pos2}")

        bnd = self.bounds
        cells = self.cells
        dx, dy = x2 - x1, y2 - y1
        length = (dx * dx + dy * dy) ** 0.5
        ldx, ldy = dx / length, dy / length
        step_x = 1 if ldx > 0 else (-1 if ldx < 0 else 0)
        step_y = 1 if ldy > 0 else (-1 if ldy < 0 else 0)
        cur_x, cur_y = x1 + 0.5, y1 + 0.5

        if ldx == 0:
            while cur_y < bnd.Y:
                ix, iy = int(cur_x), int(cur_y)
                if not (bnd.x <= ix <= bnd.X and bnd.y <= iy <= bnd.Y):
                    break
                c = cells[iy][ix]
                if ok_type is not None and not isinstance(c, ok_type):
                    break
                if bad_type is not None and isinstance(c, bad_type):
                    break
                yield c
                cur_y += step_y
        elif ldy == 0:
            while cur_x < bnd.X:
                ix, iy = int(cur_x), int(cur_y)
                if not (bnd.x <= ix <= bnd.X and bnd.y <= iy <= bnd.Y):
                    break
                c = cells[iy][ix]
                if ok_type is not None and not isinstance(c, ok_type):
                    break
                if bad_type is not None and isinstance(c, bad_type):
                    break
                yield c
                cur_x += step_x
        else:
            tdelta_x, tdelta_y = abs(step_x / ldx), abs(step_y / ldy)
            tmax_x, tmax_y = tdelta_x / 2, tdelta_y / 2
            while cur_x <= bnd.X and cur_y <= bnd.Y:
                ix, iy = int(cur_x), int(cur_y)
                if not (bnd.x <= ix <= bnd.X and bnd.y <= iy <= bnd.Y):
                    break
                c = cells[iy][ix]
                if ok_type is not None and not isinstance(c, ok_type):
                    break
                if bad_type is not None and isinstance(c, bad_type):
                    break
                yield c
                if tmax_x < tmax_y:
                    tmax_x += tdelta_x
                    cur_x += step_x
                else:
                    tmax_y += tdelta_y
                    cur_y += step_y

    def fast_voxel(self, pos1, pos2, ok_type=None, bad_type=None):
        """return positions mapped by Fast Voxel: Amanatides, Woo"""

        if pos1 == pos2:
            raise ValueError(f"direction undfined for {pos1} == {pos2}")

        def type_break(cell):
            if ok_type is not None and not isinstance(cell, ok_type):
                return True
            if bad_type is not None and isinstance(cell, bad_type):
                return True
            return False

        bnd = self.bounds
        b1, b2 = Box(pos1), Box(pos2)
        l2d = b1.line_to(b2).direction
        cur = b1.center.copy()
        step = l2d.sign()

        if l2d.x == 0:
            # voxel divides by 0 while computing tdelta if l2d.x is 0
            while cur.y < bnd.Y:
                c = self[cur]
                if type_break(c):
                    break
                yield c
                cur.y += step.y

        elif l2d.y == 0:
            # voxel divides by 0 while computing tdelta if l2d.y is 0
            while cur.x < bnd.X:
                c = self[cur]
                if type_break(c):
                    break
                yield c
                cur.x += step.x

        else:
            # NOTE: the paper doesn't demonstrate how to compute tdelta and tmax.
            # You have to work that out for yourself …

            # tdelta is the amount of l2d it takes to cross one whole cell
            tdelta = step * ((b1.lr - b1.ul) / l2d)

            # tmax starts as the amount of l2d it takes to get to the next cell (b1.lr)
            tmax = tdelta / 2
            # tmax_other = (b1.lr-b1.center) / l2d
            # assert tmax == tmax_other

            while cur.x <= bnd.X and cur.y <= bnd.Y:
                # The loop is actually in the paper

                c = self[cur]
                if type_break(c):
                    break
                yield c

                if tmax.x < tmax.y:
                    tmax.x += tdelta.x
                    cur.x += step.x
                else:
                    tmax.y += tdelta.y
                    cur.y += step.y

    def _visicalc(self, pos1, pos2):
        # Stop line-of-sight at walls and closed doors; return positions up to barrier
        from .cell.blocked import BlockedCell
        from ..door import Door

        seen = set()
        for c in self.uberfast_voxel(pos1, pos2, bad_type=Wall):
            seen.add(c.pos)
            # stop at closed doors, but allow LOS through open doors
            if isinstance(c, BlockedCell):
                d = c.door
                if isinstance(d, Door) and not d.open:
                    break
            # also stop if the very next step is a wall (already handled by bad_type)
        return seen

    def visicalc(self, whom, maxdist=None):
        c1 = self[whom]
        if not isinstance(c1, Cell):
            raise ValueError(f"{whom} is not on the map apparently")
        seen = {c1.pos}
        for c in self.iter_cells():
            if c is not c1:
                seen |= self._visicalc(c1.pos, c.pos)
        if maxdist:
            maxdist = test_maxdist(maxdist)
            seen = {p for p in seen if p == c1.pos or maxdist(c1.pos, p)}
        return seen

    def maxdist_submap(self, whom, maxdist=None):
        seen = self.visicalc(whom, maxdist=maxdist)

        # we don't actually use the visicalc to bound the map view though
        wlp = whom.location.pos
        actual_bnds = self.bounds
        bnds = Bounds(wlp[0] - maxdist, wlp[1] - maxdist, wlp[0] + maxdist, wlp[1] + maxdist)
        log.debug(
            "maxdist_submap actual-bounds=[%s: %s] submap-bounds=[%s: %s]",
            actual_bnds,
            tuple(actual_bnds),
            bnds,
            tuple(bnds),
        )
        return MapView(self, bounds=bnds, whom=whom, seen=frozenset(seen))

    @lru_cache(maxsize=None)
    def visicalc_submap(self, whom, maxdist=None):
        seen = self.visicalc(whom, maxdist=maxdist)
        wlp = whom.location.pos
        bnds = Bounds(*(wlp * 2))
        for p in seen:
            if p[0] < bnds.x:
                bnds.x = p[0]
            if p[0] > bnds.X:
                bnds.X = p[0]
            if p[1] < bnds.y:
                bnds.y = p[1]
            if p[1] > bnds.Y:
                bnds.Y = p[1]
        actual_bnds = self.bounds
        maxdist = test_maxdist(maxdist)
        if bnds.x > actual_bnds.x and maxdist(wlp, (bnds.x - 1, wlp[1])):
            bnds.x -= 1
        if bnds.y > actual_bnds.y and maxdist(wlp, (wlp[0], bnds.y - 1)):
            bnds.y -= 1
        if bnds.X < actual_bnds.X and maxdist(wlp, (bnds.X + 1, wlp[1])):
            bnds.X += 1
        if bnds.Y < actual_bnds.Y and maxdist(wlp, (wlp[0], bnds.Y + 1)):
            bnds.Y += 1
        log.debug(
            "visicalc_submap actual-bounds=[%s: %s] submap-bounds=[%s: %s]",
            actual_bnds,
            tuple(actual_bnds),
            bnds,
            tuple(bnds),
        )
        return MapView(self, bounds=bnds, whom=whom, seen=frozenset(seen))

    def invalidate(self):
        self.visicalc_submap.cache_clear()

    # Hearing-like visicalc: attenuates through barriers instead of pruning LOS
    def hearicalc(self, whom, maxdist=None, min_propagation=10, spl=60):
        """
        Return {pos: level} for the positions where a sound of spl dB SPL
        made by whom is still at least min_propagation dB SPL.

        The level at a cell is spl, less the attenuation (dB) of every cell
        entered along the least-loss path, less the falloff 20·log10(r) for
        r the straight-line distance in meters (clamped at 1 m), less
        SHADOW when whom can't see the cell.  The model is approximate on
        purpose: fun and plausible, not physics.

        maxdist and min_propagation only bound the computation.
        """

        wlp = whom.location.pos
        maxdist = test_maxdist(maxdist)
        seen = self.visicalc_submap(whom).seen

        def level(p, loss):
            return spl - loss - 20 * math.log10(max(1, LineSeg(wlp, p).distance.v)) - (0 if p in seen else SHADOW)

        start = (wlp[0], wlp[1])
        best = {start: 0}
        pq = [(0, start)]
        heard = {}
        while pq:
            loss, p = heapq.heappop(pq)
            if p in heard or not maxdist(wlp, p) or (lv := level(p, loss)) < min_propagation:
                continue
            heard[p] = lv
            for np in ((p[0] + 1, p[1]), (p[0] - 1, p[1]), (p[0], p[1] + 1), (p[0], p[1] - 1)):
                if (c := self.get(*np)) is not None and (nl := loss + c.attenuation) < best.get(np, math.inf):
                    best[np] = nl
                    heapq.heappush(pq, (nl, np))
        return heard

    def hearicalc_submap(self, whom, maxdist=None, min_propagation=10):
        """
        A MapView of what `whom` can hear: bounded to the heard positions,
        with `seen` holding them, so `.cells`/`.objects` are whom's hearing.
        """

        heard = self.hearicalc(whom, maxdist=maxdist, min_propagation=min_propagation)
        xs = [p[0] for p in heard]
        ys = [p[1] for p in heard]
        return MapView(self, bounds=Bounds(min(xs), min(ys), max(xs), max(ys)), whom=whom, seen=frozenset(heard))


class MapClique(set):
    @property
    def edges(self):
        return {x for x in self if x.has_neighbor((Wall, type(None)))}


class MapView(Map):
    def __init__(self, a_map, bounds=None, filter_cells=True, whom=None, seen=None):  # pylint: disable=super-init-not-called
        self.a_map = a_map
        self._bounds = bounds
        self._filter = filter_cells
        self.whom = whom if whom is not None else a_map.whom
        self.seen = seen if seen is not None else a_map.seen

    @property
    def bounds(self):
        if self._bounds is not None:
            return self._bounds
        return self.a_map.bounds

    def _cells(self):
        """return a copy of the actual cell arrays
        the copy may be bounded, and can be filtered without ruining the
        actual cell array in self.a_map
        """
        vb = self.bounds
        ab = self.a_map.bounds
        return [[self.a_map.cells[j - ab.y][i - ab.x] if ab.contains(i, j) else None for i in vb.x_iter] for j in vb.y_iter]

        # note: we used to do the below, but we changed it 2023-06-19 to
        # faciliate genearting submaps of a specific size, even if the submap
        # would span outside the map.
        #
        #   bnds = self.bounds
        #   return [ [ self.a_map.cells[j][i] for i in bnds.x_iter ] for j in bnds.y_iter ]

    def iter_type(self, *a, **kw):
        bnds = self.bounds
        for p, cell in self.a_map.iter_type(*a, **kw):
            if bnds.contains(p):
                yield p, cell

    # iter_cells() uses iter_type(), so it's already fixed too

    def realpos(self, x, y):
        return x + self.bounds.x, y + self.bounds.y

    def get(self, x, y):
        return self.a_map.get(*self.realpos(x, y))

    @property
    def cells(self):
        cells = self._cells()
        bnds = self.bounds

        def _fake_none(p):
            qi, qj = (p[0] - bnds.x, p[1] - bnds.y)
            # log.debug('_fake_none(%s) -> (%s,%s)', p, qi,qj)
            cells[qj][qi] = None

        if self._filter:
            for cell in self.iter_cells(of_type=Cell):
                if cell.pos not in self.seen:
                    _fake_none(cell.pos)
            for cell in self.iter_cells(of_type=Wall):
                if not any(ncell is not None and ncell.pos in self.seen for _, ncell in cell.iter_neighbors(dirs=DDIRS)):
                    _fake_none(cell.pos)
        return cells
