# coding: utf-8

from math import cos, sin, tau

from space.map import Map
from space.map.cell import Floor, Corridor, Wall
from .tools import Shape, circle, disk, line, spear_room, stadium_room


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
    wall_thickness = 1.0
    shape = Shape()
    shape.merge(disk(center, hub_radius, Floor))
    shape.merge(circle(center, inner_radius, outer_radius, Corridor))
    shape.merge(circle(center, outer_radius + 0.5, outer_radius + 1.5, Wall))
    for idx in range(room_count):
        angle = tau * idx / room_count
        shape.merge(
            line(
                center,
                (
                    round(center[0] + cos(angle) * corridor_length),
                    round(center[1] + sin(angle) * corridor_length),
                ),
                corridor_width,
                Corridor,
            )
        )
        angle_span = tau / room_count
        if room_kind == "stadium":
            depth = room_depth
            radius_mid = outer_radius + 2 + depth / 2
            gap_angle = wall_thickness / max(radius_mid, 1.0)
            theta_half = max(0.01, angle_span / 2 - gap_angle / 2)
            arc_length = 2 * radius_mid * theta_half
            shape.merge(
                stadium_room(
                    center,
                    angle,
                    radius_mid,
                    depth,
                    arc_length,
                    Floor,
                )
            )
        elif room_kind == "spear":
            length = room_depth + 4
            radius_mid = outer_radius + 2 + length / 2
            width = min(room_width, 16)
            shape.merge(
                spear_room(
                    (
                        round(center[0] + cos(angle) * radius_mid),
                        round(center[1] + sin(angle) * radius_mid),
                    ),
                    angle,
                    length,
                    width,
                    Floor,
                    back_cut=0.2,
                )
            )
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
