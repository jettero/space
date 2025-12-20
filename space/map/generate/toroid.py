# coding: utf-8

from math import atan2, cos, sin, tau

from space.map import Map
from space.map.cell import Floor, Corridor, Wall
from .tools import Shape, circle, disk, line, thin_line


def generate_station(
    center=(0, 0),
    outer_radius=40,
    walkway_width=3,
    corridor_width=3,
    room_count=12,
    room_width=20,
    room_depth=5,
    room_kind="stadium",
):
    inner_radius = outer_radius - walkway_width
    hub_radius = max(6, inner_radius - 18)
    corridor_length = outer_radius
    shape = Shape()
    shape.merge(disk(center, hub_radius, Floor))
    shape.merge(circle(center, inner_radius, outer_radius, Corridor))
    for idx in range(room_count):
        angle = tau * idx / room_count
        if room_kind == "spear":
            room_radius = min(max(room_width // 3, 3), 6)
            room_center_dist = outer_radius + room_radius + 2
            corridor_end = max(corridor_length, room_center_dist - room_radius - 1)
        else:
            corridor_end = corridor_length
        shape.merge(
            line(
                center,
                (
                    round(center[0] + cos(angle) * corridor_end),
                    round(center[1] + sin(angle) * corridor_end),
                ),
                corridor_width,
                Corridor,
            )
        )
        angle_span = tau / room_count
        if room_kind == "stadium":
            wall_thickness = 1.0
            door_width = 2.0
            wall_inner = outer_radius
            wall_outer = outer_radius + wall_thickness
            floor_outer = wall_outer + room_depth
            limit = int(floor_outer) + 1
            door_angle = door_width / max(wall_inner + 0.5, 1.0)
            theta_half = angle_span / 2
            door_half = door_angle / 2
            walkway_gap = 0.6 / max(wall_outer, 1.0)
            wall_cells = set()
            floor_cells = set()
            cx, cy = center
            inner_sq = wall_inner * wall_inner
            wall_sq = wall_outer * wall_outer
            outer_sq = floor_outer * floor_outer
            for y in range(int(cy - limit), int(cy + limit) + 1):
                for x in range(int(cx - limit), int(cx + limit) + 1):
                    dx = x - cx
                    dy = y - cy
                    dist_sq = dx * dx + dy * dy
                    if dist_sq <= inner_sq or dist_sq > outer_sq:
                        continue
                    theta = atan2(dy, dx)
                    delta = (theta - angle + tau) % tau
                    if delta > tau / 2:
                        delta -= tau
                    abs_delta = abs(delta)
                    if abs_delta > theta_half:
                        continue
                    if dist_sq <= wall_sq:
                        if abs_delta <= door_half:
                            floor_cells.add((x, y))
                        elif abs_delta <= theta_half - walkway_gap:
                            wall_cells.add((x, y))
                        # otherwise leave empty so radial wall handles boundary
                        continue
                    if abs_delta < theta_half:
                        floor_cells.add((x, y))
            boundary_cells = set()
            for sign in (-1, 1):
                boundary_angle = angle + sign * theta_half
                start = (
                    round(cx + cos(boundary_angle) * wall_outer),
                    round(cy + sin(boundary_angle) * wall_outer),
                )
                end = (
                    round(cx + cos(boundary_angle) * floor_outer),
                    round(cy + sin(boundary_angle) * floor_outer),
                )
                for pos in thin_line(start, end):
                    if (pos[0] - cx) ** 2 + (pos[1] - cy) ** 2 < wall_sq:
                        continue
                    boundary_cells.add(pos)
            floor_cells.difference_update(boundary_cells)
            wall_cells.update(boundary_cells)
            shape.add(Wall, wall_cells)
            shape.add(Floor, floor_cells)
            continue
        elif room_kind == "spear":
            room_center = (
                round(center[0] + cos(angle) * room_center_dist),
                round(center[1] + sin(angle) * room_center_dist),
            )
            shape.merge(disk(room_center, room_radius, Floor))
            for step in range(1, min(2, room_radius) + 1):
                px = round(center[0] + cos(angle) * (corridor_end + step))
                py = round(center[1] + sin(angle) * (corridor_end + step))
                shape.add(Floor, {(px, py)})
        else:
            raise ValueError(f"unknown room_kind: {room_kind}")
    return build_map(shape, Wall)


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
