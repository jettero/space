# coding: utf-8

from math import cos, sin, tau

from space.map import Map
from space.map.cell import Floor, Corridor, Wall
from .tools import Shape, circle, disk, line, stadium_room


def generate_station(
    center=(0, 0),
    outer_radius=40,
    walkway_width=5,
    corridor_width=3,
    room_count=12,
    room_width=6,
    room_depth=6,
):
    inner_radius = outer_radius - walkway_width
    hub_radius = max(6, inner_radius - 18)
    corridor_length = outer_radius + room_depth
    shape = Shape()
    shape.merge(disk(center, hub_radius, Floor))
    shape.merge(circle(center, inner_radius, outer_radius, Corridor))
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
        shape.merge(
            stadium_room(
                (
                    round(center[0] + cos(angle) * (outer_radius + room_depth / 2 + 1)),
                    round(center[1] + sin(angle) * (outer_radius + room_depth / 2 + 1)),
                ),
                angle,
                room_depth,
                room_width,
                Floor,
            )
        )
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
