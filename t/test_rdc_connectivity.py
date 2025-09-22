# coding: utf-8

import pytest

from space.map.generate.rdc import generate
from space.map.cell import Cell, Wall


def neighbors4(p):
    x, y = p
    return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]


def dijkstra_cells(a_map, starts):
    import heapq

    dist = {}
    pq = []
    for s in starts:
        dist[s] = 0
        heapq.heappush(pq, (0, s))
    while pq:
        d, u = heapq.heappop(pq)
        if d != dist[u]:
            continue
        for v in neighbors4(u):
            if not a_map.in_bounds(*v):
                continue
            cv = a_map[v]
            if not isinstance(cv, Cell):
                continue
            nd = d + 1
            if nd < dist.get(v, 1 << 60):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist


def flood_fill_cells(a_map, start, visited):
    stack = [start]
    comp = set()
    while stack:
        p = stack.pop()
        if p in visited:
            continue
        visited.add(p)
        comp.add(p)
        for v in neighbors4(p):
            if not a_map.in_bounds(*v):
                continue
            if isinstance(a_map[v], Cell):
                stack.append(v)
    return comp


def has_door_on_perimeter(a_map, room_cells):
    # A door is a Cell on the perimeter where an adjacent Wall also borders a Cell (room interior)
    # and on the opposite side of that Wall there is a corridor Cell.
    room_set = set(room_cells)
    for p in room_cells:
        x, y = p
        # perimeter if any neighbor is Wall
        for nx, ny in neighbors4(p):
            if not a_map.in_bounds(nx, ny):
                continue
            n = a_map[nx, ny]
            if isinstance(n, Wall):
                # Check corridor on other side of the wall
                ox, oy = (nx + (nx - x), ny + (ny - y))
                if not a_map.in_bounds(ox, oy):
                    continue
                o = a_map[ox, oy]
                if isinstance(o, Cell) and (ox, oy) not in room_set:
                    return True
    return False


def test_rdc_map_connectivity_and_enclosure():
    # Try a couple seeds to reduce flakiness while generation stabilizes
    m = generate(x=40, y=30)

    # collect all corridor/room cells
    cells = [p for p, c in m if isinstance(c, Cell)]
    # Identify contiguous cell regions (rooms/corridors mixed), then decide playable set:
    visited = set()
    components = []
    for p in cells:
        if p in visited:
            continue
        comp = flood_fill_cells(m, p, visited)
        components.append(comp)

    assert cells, "generator produced no cells"

    # enclosure: each cell must be surrounded N,S,E,W by either Wall or Cell (never None)
    for x, y in cells:
        for nx, ny in neighbors4((x, y)):
            if not m.in_bounds(nx, ny):
                # out of bounds is not allowed (no way to place walls)
                pytest.fail(f"cell at edge without enclosure: {(x, y)}")
            c = m[nx, ny]
            assert isinstance(c, (Cell, Wall)), f"unenclosed cell neighbor at {(nx, ny)} around {(x, y)}"

    # connectivity: all Cells should be in a single component and mutually reachable
    assert len(components) == 1, f"map not fully connected: {len(components)} components"
    # run Dijkstra from an arbitrary cell and ensure all cells are reachable
    src = cells[0]
    dist = dijkstra_cells(m, [src])
    missing = [p for p in cells if p not in dist]
    assert not missing, f"unreachable cells from {src}: {missing[:10]} (and {max(0, len(missing)-10)} more)"
