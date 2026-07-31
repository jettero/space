# coding: utf-8

from space.map import Map
from space.map.cell import Floor, Corridor, Wall
from .tools import Shape, octagon, octagon_ring, axis_corridor, diagonal_corridor, rectangle, AXIS, DIAG, STEP


def generate_station(
    center=(0, 0),
    hub_r1=8,
    hub_r2=11,
    ring_r1=26,
    ring_r2=36,
    walkway_width=3,
    corridor_width=3,
    room_size=7,
    room_kind="bay",
):
    """Build an octagonal space station whose every wall edge is axis-aligned or
    an exact 45 degree diagonal, so it renders cleanly at one cell per char.

    Layout: an octagonal walkway ring (Corridor), a central octagonal hub
    (Floor), eight radial corridors (one per renderable direction: n/s/e/w axis
    lines and ne/nw/se/sw exact-45 degree lines), and a rectangular room at the
    end of each spoke. room_kind "bay" seats the rooms flush against the ring;
    "module" detaches them outside it and extends each spoke to reach.
    """

    if room_kind not in ("bay", "module"):
        raise ValueError(f"unknown room_kind: {room_kind}")
    cx, cy = center
    shape = Shape()
    shape.merge(octagon_ring(center, ring_r1, ring_r2, walkway_width, Corridor))
    shape.merge(octagon(center, hub_r1, hub_r2, Floor))
    gap = 0 if room_kind == "bay" else room_size + 1
    for d in AXIS + DIAG:
        reach = (ring_r1 if d in AXIS else ring_r2 // 2) + gap
        corridor = axis_corridor if d in AXIS else diagonal_corridor
        shape.merge(corridor(center, d, reach, corridor_width, Corridor))
        dx, dy = STEP[d]
        shape.merge(rectangle((cx + dx * reach, cy + dy * reach), room_size, room_size, Floor))
    return build_map(shape, Wall)


_DIAG = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def corner_gaps(occupied, walls):
    """Void cells where a horizontal wall run meets a vertical wall run at a
    right angle. Filling them turns the ╶ ╷ stubs at rectangular corners into
    proper ┌┐└┘, while leaving 45 degree hull edges alone (their walls are
    diagonal, never paired horizontal+vertical runs).
    """

    def hpair(x, y):
        return (x, y) in walls and ((x - 1, y) in walls or (x + 1, y) in walls)

    def vpair(x, y):
        return (x, y) in walls and ((x, y - 1) in walls or (x, y + 1) in walls)

    gaps = set()
    for fx, fy in occupied:
        for dx, dy in _DIAG:
            x, y = fx + dx, fy + dy
            if (x, y) in occupied or (x, y) in walls:
                continue
            if (hpair(x - 1, y) or hpair(x + 1, y)) and (vpair(x, y - 1) or vpair(x, y + 1)):
                gaps.add((x, y))
    return gaps


def build_map(shape, wall_cls):
    tiles = {}
    for cell_cls, positions in shape.cells.items():
        for pos in positions:
            tiles[pos] = cell_cls
    if not tiles:
        raise ValueError("generated shape is empty")
    occupied = set(tiles)
    walls = set()
    for pos in occupied:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (neighbor := (pos[0] + dx, pos[1] + dy)) not in occupied:
                walls.add(neighbor)
    for pos in walls:
        if pos not in tiles:
            tiles[pos] = wall_cls
    for pos in corner_gaps(occupied, walls):
        tiles[pos] = wall_cls
    min_x = min(x for x, _ in tiles)
    max_x = max(x for x, _ in tiles)
    min_y = min(y for _, y in tiles)
    max_y = max(y for _, y in tiles)
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    station_map = Map(width, height)
    for (x, y), cell_cls in tiles.items():
        station_map[x - min_x, y - min_y] = cell_cls()
    return station_map
