"""
RDC (Room Dropper with Corridors)

Generates dungeon maps by first dropping spaced rooms, then carving straighter
corridors (hallways) between and around them with a set of polishing passes.

Phases
- Room drop: non-touching rooms (min_gap) via rdropper.generate_rooms.
- Seed corridors: straight-biased random walks (inertia/turn_prob) that avoid
  tight curls and parallel 1-cell wall fuzz.
- Connectivity: connect all rooms/corridors together; final map is fully
  connected (every walkable Cell reaches every other).
- Loop polish: add short straight connectors to reduce dead-end hallways.
- Prune: remove dangling stubs; safer near room doors.
- Cleanup: rebuild enclosure walls, remove corridor-splitting walls, and condense.

Tuning knobs are accepted as ints or numeric strings (e.g. '12') to mirror
legacy style.
"""

import random
import logging

from ..cell import Cell, Corridor, Floor, Wall
from ..dir_util import translate_dir

from .base import sparse
from .rdropper import generate_rooms

log = logging.getLogger(__name__)


def select_wall(a_map):
    def _useful(a_cell):
        for d in "nsew":
            if a_cell.dtype(d, Cell):
                o = a_cell.r_dpos(d)
                if a_map.in_bounds(*o):
                    return True

    walls = [a_cell for pos, a_cell in a_map.iter_type(Wall) if _useful(a_cell)]
    if not walls:
        return None
    return random.choice(walls)


def add_corridor(a_map, max_steps=200, inertia=4, turn_prob=0.15):
    """Carve a straighter corridor with spacing rules to avoid curls.
    - inertia: prefer continuing straight up to this many steps
    - turn_prob: chance to allow turns even if straight is available
    """
    nonetype = type(None)
    seed = select_wall(a_map)
    if seed is None:
        log.debug("add_corridor: no suitable wall seed found; skipping")
        return
    pos = seed.pos
    a_map[pos] = Corridor(mobj=a_map, pos=pos)
    log.debug("add_corridor: seeding corridor at %s", pos)

    def ok_target(q):
        b = a_map.bounds
        # keep one cell inside the border so enclosure can be built
        if q[0] <= 0 or q[1] <= 0 or q[0] >= b[2] - 1 or q[1] >= b[3] - 1:
            return False
        # spacing rule: avoid carving adjacent to existing corridors diagonally
        for dd in ["n", "s", "e", "w", "ne", "nw", "se", "sw"]:
            qp = translate_dir(dd, q)
            if a_map.in_bounds(*qp) and isinstance(a_map[qp], Cell):
                # allow if this neighbor is exactly the seed we're extending from
                if qp != pos:
                    return False
        # avoid knocking out room corners: don't carve if q touches a Cell only diagonally
        diag_cells = 0
        ortho_cells = 0
        for dd in ["n", "s", "e", "w"]:
            qp = translate_dir(dd, q)
            if a_map.in_bounds(*qp) and isinstance(a_map[qp], Cell):
                ortho_cells += 1
        for dd in ["ne", "nw", "se", "sw"]:
            qp = translate_dir(dd, q)
            if a_map.in_bounds(*qp) and isinstance(a_map[qp], Cell):
                diag_cells += 1
        if diag_cells and not ortho_cells:
            return False
        return True

    d = None
    straight_left = 0
    steps = 0
    while steps < max_steps:
        steps += 1
        # candidates are closed neighbor walls that pass spacing rule
        cand = []
        for nd in "nsew":
            nq = translate_dir(nd, pos)
            if isinstance(a_map[nq], nonetype) or isinstance(a_map[nq], Wall):
                if ok_target(nq):
                    cand.append(nd)
        if not cand:
            log.debug("add_corridor: no candidates from %s; stopping at step=%d", pos, steps)
            break
        if d in cand and (straight_left > 0 and random.random() > turn_prob):
            ndir = d
            straight_left -= 1
        else:
            ndir = random.choice(cand)
            straight_left = inertia - 1
        pos = translate_dir(ndir, pos)
        a_map[pos] = Corridor(mobj=a_map, pos=pos)
        log.debug("add_corridor: carved to %s dir=%s", pos, ndir)
        d = ndir
        # stop if we hit a junction (>=2 open neighbors)
        c = a_map[pos]
        open_neighbors = sum(1 for n in (c.n, c.s, c.e, c.w) if isinstance(n, Cell))
        if open_neighbors >= 2:
            log.debug("add_corridor: hit junction at %s; stopping", pos)
            break


def reconstruct_walls(a_map):
    """Ensure corridor side walls exist around Cells. Does not modify room interiors."""
    nonetype = type(None)
    to_wall = []
    for (i, j), c in a_map:
        if isinstance(c, Cell):
            for dd in ["n", "s", "e", "w", "ne", "nw", "se", "sw"]:
                p = translate_dir(dd, (i, j))
                if not a_map.in_bounds(*p):
                    continue
                q = a_map[p]
                if isinstance(q, nonetype):
                    to_wall.append(p)
    for p in to_wall:
        a_map[p] = Wall(mobj=a_map, pos=p)
    if to_wall:
        log.debug("reconstruct_walls: added %d enclosure walls", len(to_wall))
    # Remove walls that sit between two corridor cells (useless walls)
    for (i, j), c in list(a_map):
        if not isinstance(c, Wall):
            continue
        # If any opposite neighbors are both Cells, open this wall
        if (
            a_map.in_bounds(i + 1, j)
            and a_map.in_bounds(i - 1, j)
            and isinstance(a_map[i + 1, j], Cell)
            and isinstance(a_map[i - 1, j], Cell)
        ):
            a_map[i, j] = Corridor(mobj=a_map, pos=(i, j))
            log.debug("reconstruct_walls: removed E/W split wall at (%d,%d)", i, j)
            continue
        if (
            a_map.in_bounds(i, j + 1)
            and a_map.in_bounds(i, j - 1)
            and isinstance(a_map[i, j + 1], Cell)
            and isinstance(a_map[i, j - 1], Cell)
        ):
            a_map[i, j] = Corridor(mobj=a_map, pos=(i, j))
            log.debug("reconstruct_walls: removed N/S split wall at (%d,%d)", i, j)
            continue


def _room_edges(a_map):
    """Yield tuples (pos, cell) for wall cells on room perimeters."""
    edges = []
    for (i, j), c in a_map:
        if not isinstance(c, Wall):
            continue
        # perimeter wall must have a Cell on one side and space/None/Wall on the other
        if c.has_neighbor(of_type=Cell):
            edges.append((i, j))
    return edges


def _path_to_nearest_corridor(a_map, start_pos):
    """Constrained BFS from start_pos (a wall on room perimeter) to nearest corridor Cell.
    Respects spacing: avoids adjacency to existing corridors except at the final target.
    Returns a list of positions (including start_pos, excluding the existing corridor cell).
    """
    from collections import deque

    def spacing_ok(p, target=None):
        for dd in ["n", "s", "e", "w", "ne", "nw", "se", "sw"]:
            q = translate_dir(dd, p)
            if not a_map.in_bounds(*q):
                continue
            if isinstance(a_map[q], Cell) and q != target:
                return False
        return True

    seen = set([start_pos])
    q = deque([(start_pos, [])])
    while q:
        p, path = q.popleft()
        # reached corridor?
        if isinstance(a_map[p], Cell) and p != start_pos:
            return path  # path leads up to the cell before p already carved
        for d in "nsew":
            np = translate_dir(d, p)
            if np in seen or not a_map.in_bounds(*np):
                continue
            # don't go through room interiors; allow None/Wall
            qc = a_map[np]
            if isinstance(qc, Cell):
                # allow if we are reaching the target corridor
                if spacing_ok(np, target=np):
                    return path + [np]
                continue
            if not spacing_ok(np):
                continue
            seen.add(np)
            q.append((np, path + [np]))
    return []


def connect_disconnected_rooms(a_map):
    """Ensure each room touches the corridor network by carving from room edge to nearest corridor."""
    edges = _room_edges(a_map)
    if not edges:
        return
    used_doors = set()
    for ex, ey in edges:
        # if already adjacent to corridor, skip
        w = a_map[ex, ey]
        has_adj = any(isinstance(getattr(w, d), Cell) for d in ("n", "s", "e", "w"))
        if has_adj:
            continue
        # pick a single door per contiguous wall segment: avoid clustering doors
        if (ex, ey) in used_doors:
            continue
        path = _path_to_nearest_corridor(a_map, (ex, ey))
        if not path:
            # as a fallback, open a short door outward to create at least one playable door
            for d in "nsew":
                p = translate_dir(d, (ex, ey))
                if not a_map.in_bounds(*p):
                    continue
                if isinstance(a_map[p], Wall):
                    # try one more step; if outside is not a room interior, carve 1-cell corridor
                    p2 = translate_dir(d, p)
                    if a_map.in_bounds(*p2) and not isinstance(a_map[p2], Cell):
                        a_map[ex, ey] = Corridor(mobj=a_map, pos=(ex, ey))
                        a_map[p] = Corridor(mobj=a_map, pos=p)
                        log.debug("connect_disconnected_rooms: fallback door at %s dir=%s", (ex, ey), d)
                        reconstruct_walls(a_map)
                        used_doors.add((ex, ey))
                        break
            continue
        # open door at the room edge and carve the path
        a_map[ex, ey] = Corridor(mobj=a_map, pos=(ex, ey))
        for p in path:
            a_map[p] = Corridor(mobj=a_map, pos=p)
        log.debug("connect_disconnected_rooms: carved %d cells from %s to corridor", len(path), (ex, ey))
        used_doors.add((ex, ey))
        reconstruct_walls(a_map)
    # Ensure global connectivity between rooms: if multiple components exist, add doors/links
    try:
        ensure_room_connectivity(a_map)
    except Exception:
        # keep generation robust even if connectivity fails; walls were reconstructed already
        pass


def ensure_room_connectivity(a_map):
    """Ensure all Cell tiles form a single connected component by adding connectors.

    Strategy: identify Cell components via flood fill. While more than one
    component exists, connect the closest pair by carving a straight-ish path
    between their nearest border Cells, then reconstruct walls. Repeat until
    one component remains or no progress is possible.
    """
    from collections import deque

    def cell_neighbors(p):
        x, y = p
        for v in [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]:
            if a_map.in_bounds(*v) and isinstance(a_map[v], Cell):
                yield v

    def flood(start, visited):
        comp = set()
        dq = deque([start])
        visited.add(start)
        while dq:
            u = dq.popleft()
            comp.add(u)
            for v in cell_neighbors(u):
                if v not in visited:
                    visited.add(v)
                    dq.append(v)
        return comp

    def components():
        seen = set()
        comps = []
        for (i, j), c in a_map:
            if isinstance(c, Cell) and (i, j) not in seen:
                comps.append(flood((i, j), seen))
        return comps

    def nearest_points(a, b):
        # return pair (pa, pb) with minimal Manhattan distance
        best = None
        bd = None
        for pa in a:
            ax, ay = pa
            for pb in b:
                bx, by = pb
                d = abs(ax - bx) + abs(ay - by)
                if bd is None or d < bd:
                    bd = d
                    best = (pa, pb)
        return best

    def carve_path(a, b):
        # simple L-shaped carve with spacing awareness
        ax, ay = a
        bx, by = b
        path = []
        x, y = ax, ay
        sx = 1 if bx > x else -1
        sy = 1 if by > y else -1
        while x != bx:
            x += sx
            path.append((x, y))
        while y != by:
            y += sy
            path.append((x, y))
        for p in path:
            if not a_map.in_bounds(*p):
                return False
            if not isinstance(a_map[p], Cell):
                a_map[p] = Corridor(mobj=a_map, pos=p)
        return True

    # Iteratively connect components until one remains
    for _ in range(64):  # safety cap
        comps = components()
        if len(comps) <= 1:
            break
        # connect the two largest components first
        comps.sort(key=len, reverse=True)
        a, b = comps[0], comps[1]
        pa, pb = nearest_points(a, b)
        if not carve_path(pa, pb):
            break
        log.debug("ensure_room_connectivity: connected components at %s -> %s", pa, pb)
        reconstruct_walls(a_map)


def generate(
    x=50,
    y=50,
    rsz="2d4+1",
    rsparse="1d10+3",
    # room spacing
    min_gap=1,
    # initial corridor seeding (numbers or strings)
    seed_budget=None,
    inertia="5",
    turn_prob="10",
    max_steps="180",
    # loop creation (higher chance reduces dead-ends)
    loop_chance="18",
    loop_max_len="14",
    # pruning (keep more near doors; reduces harsh trimming)
    prune_keep_depth="3",
):
    """Generate a map with rooms and corridors (RDC).

    Parameters (ints or numeric strings):
    - min_gap: minimum empty cells between rooms (default 1)
    - seed_budget: number of initial corridor seeds (default ≈ area/400)
    - inertia: steps to prefer going straight (default 5)
    - turn_prob: percent chance to allow a turn even if straight (default 10)
    - max_steps: max steps per seed corridor (default 180)
    - loop_chance: percent chance per corridor cell to add a short straight loop (default 18)
    - loop_max_len: maximum straight length for loop connectors (default 14)
    - prune_keep_depth: keep depth near doors when pruning (default 3)

    Defaults are tuned to reduce dead-end hallways by increasing straight
    preference, slightly shortening seeds, creating more short connectors, and
    being less aggressive when pruning near doors.
    """

    def _ival(v, default):
        try:
            return int(v)
        except Exception:
            return default

    inertia_i = _ival(inertia, 4)
    turn_prob_f = _ival(turn_prob, 15) / 100.0
    max_steps_i = _ival(max_steps, 200)
    loop_chance_f = _ival(loop_chance, 12) / 100.0
    loop_max_len_i = _ival(loop_max_len, 12)
    prune_keep_i = _ival(prune_keep_depth, 2)

    a_map = generate_rooms(x=x, y=y, rsz=rsz, rsparse=rsparse, cellify_partitions=True, min_gap=min_gap)
    # Tag initial room cells so pruning passes never remove room interiors.
    room_cells = set()
    for (i, j), c in a_map:
        if isinstance(c, Cell):
            room_cells.add((i, j))
            c.tags.add("room_cell")
    log.debug("generate: tagged %d room cells", len(room_cells))
    # Seed a few straight-ish corridors
    budget = max(3, int((x * y) / 400)) if seed_budget is None else _ival(seed_budget, 3)
    for _ in range(budget):
        add_corridor(a_map, max_steps=max_steps_i, inertia=inertia_i, turn_prob=turn_prob_f)
    reconstruct_walls(a_map)
    # Ensure rooms connect to corridors
    connect_disconnected_rooms(a_map)
    # Optional small loop creation pass: connect nearby corridors sparingly
    add_small_loops(a_map, chance=loop_chance_f, max_len=loop_max_len_i)
    reconstruct_walls(a_map)
    # Prune excessive dead-ends that don't terminate at a room door
    prune_deadends(a_map, keep_door_depth=prune_keep_i)
    a_map.strip_useless_walls()
    # Add doors where corridors meet rooms
    a_map.place_doors()
    a_map.condense()
    return a_map


def _corridor_neighbors(c):
    return [n for n in (c.n, c.s, c.e, c.w) if isinstance(n, Cell)]


def add_small_loops(a_map, chance=0.12, max_len=12):
    """Occasionally connect nearby corridors to reduce dead ends, avoiding curls."""
    for (i, j), c in list(a_map):
        if not isinstance(c, Cell):
            continue
        # chance gate
        import random as _r

        if _r.random() > chance:
            continue
        # try to reach another corridor in straight-ish short run
        for d in "nsew":
            steps = 0
            p = (i, j)
            ok = True
            while steps < max_len:
                steps += 1
                p = translate_dir(d, p)
                if not a_map.in_bounds(*p):
                    ok = False
                    break
                if isinstance(a_map[p], Cell):
                    break
                # avoid tight adjacency
                for dd in ["n", "s", "e", "w", "ne", "nw", "se", "sw"]:
                    q = translate_dir(dd, p)
                    if a_map.in_bounds(*q) and isinstance(a_map[q], Cell):
                        ok = False
                        break
                if not ok:
                    break
            else:
                ok = False
            if ok and isinstance(a_map[p], Cell) and steps > 1:
                # carve the link
                p2 = (i, j)
                for _ in range(steps - 1):
                    p2 = translate_dir(d, p2)
                    a_map[p2] = Cell(mobj=a_map, pos=p2)
                log.debug("add_small_loops: added %d straight link(s) from (%d,%d) dir=%s", steps - 1, i, j, d)
                break


def prune_deadends(a_map, keep_door_depth=3, min_prune_len=2):
    """Remove corridor stubs while preserving access to doors and connectivity.

    Algorithm:
    - Identify degree-1 corridor Cells (dead-end tips).
    - For each tip, walk inward up to `keep_door_depth` if near a door (a wall
      adjacent to the current Cell that also borders a room Cell), then continue
      up to `min_prune_len` and beyond, converting Cells to Walls until reaching
      a junction (degree != 1) or a door-adjacent region we must keep.
    - Iterate until no changes. Rebuild and clean walls between passes.
    """

    def degree(p):
        x, y = p
        c = a_map[x, y]
        return sum(
            1
            for d in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
            if a_map.in_bounds(*d) and isinstance(a_map[d], Cell)
        )

    def touches_door(p):
        x, y = p
        w = a_map[x, y]
        for d in ("n", "s", "e", "w"):
            ww = getattr(w, d)
            if isinstance(ww, Wall) and ww.has_neighbor(of_type=Cell):
                return True
        return False

    def is_room_cell(p):
        c = a_map[p]
        try:
            return "room_cell" in c.tags
        except Exception:
            return False

    changed = True
    while changed:
        changed = False
        # collect all current tips
        tips = [
            (i, j)
            for (i, j), c in list(a_map)
            if isinstance(c, Cell) and degree((i, j)) == 1 and not is_room_cell((i, j))
        ]
        if tips:
            log.debug("prune_deadends: found %d tip(s)", len(tips))
        for tip in tips:
            p = tip
            kept = 0
            # preserve a short section near doors
            while touches_door(p) and kept < keep_door_depth:
                # step towards the unique neighbor
                x, y = p
                nn = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                nn = [q for q in nn if a_map.in_bounds(*q) and isinstance(a_map[q], Cell)]
                if not nn:
                    break
                p = nn[0]
                kept += 1
            # now prune forward while still in a 1-degree corridor
            pruned = 0
            q = tip
            while True:
                if not isinstance(a_map[q], Cell) or degree(q) != 1:
                    break
                if is_room_cell(q):
                    log.debug("prune_deadends: reached room cell at %s; stop", q)
                    break
                if pruned < min_prune_len or not touches_door(q):
                    a_map[q] = Wall(mobj=a_map, pos=q)
                    changed = True
                    pruned += 1
                else:
                    # hitting door-adjacent region; stop pruning this branch
                    break
                # move to next along the stub
                x, y = q
                nn = [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
                nn = [r for r in nn if a_map.in_bounds(*r) and isinstance(a_map[r], Cell)]
                if not nn:
                    break
                q = nn[0]
        if changed:
            a_map.condense()
            a_map.strip_useless_walls()
            reconstruct_walls(a_map)
            log.debug("prune_deadends: pruning pass complete")
    return a_map
