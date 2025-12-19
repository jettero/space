# coding: utf-8

from collections import defaultdict
from math import atan2, cos, pi, sin, sqrt


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


def disk(center, radius, cell_cls):
    cx, cy = center
    radius_sq = radius * radius
    points = set()
    for y in range(cy - radius, cy + radius + 1):
        for x in range(cx - radius, cx + radius + 1):
            if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= radius_sq:
                points.add((x, y))
    return Shape().add(cell_cls, points)


def circle(center, inner_radius, outer_radius, cell_cls):
    cx, cy = center
    inner_sq = inner_radius * inner_radius
    outer_sq = outer_radius * outer_radius
    points = set()
    bound = int(outer_radius) + 1
    for y in range(cy - bound, cy + bound + 1):
        for x in range(cx - bound, cx + bound + 1):
            if inner_sq <= (x - cx) * (x - cx) + (y - cy) * (y - cy) <= outer_sq:
                points.add((x, y))
    return Shape().add(cell_cls, points)


def line(start, end, width, cell_cls):
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    span = max(abs(dx), abs(dy))
    if span == 0:
        return Shape().add(cell_cls, {(sx, sy)})
    half = width / 2
    denom = sqrt(dx * dx + dy * dy)
    pts = set()
    min_x = min(sx, ex) - width
    max_x = max(sx, ex) + width
    min_y = min(sy, ey) - width
    max_y = max(sy, ey) + width
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if ((x - sx) * (x - ex) + (y - sy) * (y - ey)) > 0:
                continue
            if denom == 0:
                pts.add((x, y))
                continue
            if ((dy * x - dx * y + ex * sy - ey * sx) / denom) ** 2 <= half * half:
                pts.add((x, y))
    return Shape().add(cell_cls, pts)


def spear_room(center, angle, length, width, cell_cls, back_cut=0.35):
    cx, cy = center
    radial = (cos(angle), sin(angle))
    tangential = (-radial[1], radial[0])
    semi_major = length / 2
    semi_minor = width / 2
    limit = int(length + width) + 2
    pts = set()
    for y in range(cy - limit, cy + limit + 1):
        for x in range(cx - limit, cx + limit + 1):
            dx = x - cx
            dy = y - cy
            rel_r = dx * radial[0] + dy * radial[1]
            rel_t = dx * tangential[0] + dy * tangential[1]
            if rel_r < -semi_major * back_cut or rel_r > semi_major:
                continue
            if semi_minor == 0:
                continue
            if ((rel_r - semi_major / 2) / semi_major) ** 2 + (rel_t / semi_minor) ** 2 <= 1:
                pts.add((x, y))
    return Shape().add(cell_cls, pts)


def stadium_room(origin, angle, radius, depth, arc_length, cell_cls):
    ox, oy = origin
    inner_radius = max(0.0, radius - depth / 2)
    outer_radius = radius + depth / 2
    mid_radius = (inner_radius + outer_radius) / 2
    theta_half = arc_length / (2 * mid_radius) if mid_radius > 0 else pi
    limit = int(outer_radius + 2)
    pts = set()
    for y in range(int(oy - limit), int(oy + limit) + 1):
        for x in range(int(ox - limit), int(ox + limit) + 1):
            dx = x - ox
            dy = y - oy
            dist = sqrt(dx * dx + dy * dy)
            if dist < inner_radius or dist > outer_radius:
                continue
            theta = atan2(dy, dx)
            delta = (theta - angle + pi) % (2 * pi) - pi
            if abs(delta) <= theta_half:
                pts.add((x, y))
    return Shape().add(cell_cls, pts)
