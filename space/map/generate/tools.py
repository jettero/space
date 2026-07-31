# coding: utf-8

from collections import defaultdict

STEP = {
    "n": (0, -1),
    "s": (0, 1),
    "e": (1, 0),
    "w": (-1, 0),
    "ne": (1, -1),
    "nw": (-1, -1),
    "se": (1, 1),
    "sw": (-1, 1),
}

AXIS = ("n", "s", "e", "w")
DIAG = ("ne", "nw", "se", "sw")


class Shape:
    def __init__(self):
        self.cells = defaultdict(set)

    def add(self, cell_cls, positions):
        if positions:
            self.cells[cell_cls].update(positions)
        return self

    def merge(self, other):
        for cell_cls, positions in other.cells.items():
            if positions:
                self.cells[cell_cls].update(positions)
        return self

    def shifted(self, dx, dy):
        new_shape = Shape()
        for cell_cls, positions in self.cells.items():
            new_shape.cells[cell_cls] = {(x + dx, y + dy) for x, y in positions}
        return new_shape


def _octagon_points(cx, cy, r1, r2):
    """Filled octagon: square (|dx|,|dy|<=r1) intersected with diamond (|dx|+|dy|<=r2).

    Yields 4 axis-aligned edges (at +-r1) and 4 exact-45 degree corner
    chamfers (along |dx|+|dy|==r2), so every boundary edge rasterizes to a
    clean staircase.
    """

    return {
        (x, y) for y in range(cy - r1, cy + r1 + 1) for x in range(cx - r1, cx + r1 + 1) if abs(x - cx) + abs(y - cy) <= r2
    }


def octagon(center, r1, r2, cell_cls):
    if not r1 < r2 < 2 * r1:
        raise ValueError(f"octagon needs r1 < r2 < 2*r1 (got r1={r1}, r2={r2})")
    return Shape().add(cell_cls, _octagon_points(center[0], center[1], r1, r2))


def octagon_ring(center, r1, r2, thickness, cell_cls):
    cx, cy = center
    outer = _octagon_points(cx, cy, r1, r2)
    inner = _octagon_points(cx, cy, r1 - thickness, r2 - thickness)
    return Shape().add(cell_cls, outer - inner)


def rectangle(center, width, height, cell_cls):
    cx, cy = center
    hw, hh = width // 2, height // 2
    return Shape().add(
        cell_cls,
        {(x, y) for y in range(cy - hh, cy + hh + 1) for x in range(cx - hw, cx + hw + 1)},
    )


def axis_corridor(center, direction, length, width, cell_cls):
    cx, cy = center
    dx, dy = STEP[direction]
    half = width // 2
    pts = set()
    for step in range(length + 1):
        bx, by = cx + dx * step, cy + dy * step
        for off in range(-half, half + 1):
            pts.add((bx, by + off) if dx else (bx + off, by))
    return Shape().add(cell_cls, pts)


def diagonal_corridor(center, direction, length, width, cell_cls):
    """A solid, 4-connected diagonal band: `width` parallel exact-45 degree
    lines offset one cell apart, giving 45 degree long edges and axis-aligned
    caps. Width must be >= 2 for 4-connectivity (odd widths center on `center`).
    """

    cx, cy = center
    dx, dy = STEP[direction]
    half = width // 2
    pts = set()
    for k in range(-half, half + 1):
        for t in range(length + 1):
            pts.add((cx + dx * t + k, cy + dy * t))
    return Shape().add(cell_cls, pts)
