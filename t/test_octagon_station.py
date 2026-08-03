# coding: utf-8

import pytest

from space.map.base import Map
from space.map.cell import Cell, Wall
from space.map.generate import generate_station

ORTHO = ((1, 0), (-1, 0), (0, 1), (0, -1))


def cells_of(m):
    return {p for p, c in m if isinstance(c, Cell)}


def flood(m, start, walkable):
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()
        for dx, dy in ORTHO:
            if (n := (x + dx, y + dy)) in walkable and n not in seen:
                seen.add(n)
                stack.append(n)
    return seen


@pytest.fixture(scope="module", params=("bay", "module"))
def station(request):
    return generate_station(room_kind=request.param)


def test_station_is_sane(station):
    assert isinstance(station, Map)
    assert any(isinstance(c, Cell) for _, c in station)
    assert station.sparseness < 1.0


def test_station_walkable_connected(station):
    walkable = cells_of(station)
    assert walkable
    assert flood(station, next(iter(walkable)), walkable) == walkable


def test_station_hull_sealed(station):
    for (x, y), c in station:
        if isinstance(c, Cell):
            for dx, dy in ORTHO:
                assert station.get(x + dx, y + dy) is not None, f"floor {(x, y)} exposed to void"


def test_station_walls_all_drawable(station):
    for (x, y), c in station:
        if isinstance(c, Wall) and any(isinstance(station.get(x + dx, y + dy), Cell) for dx, dy in ORTHO):
            assert c.abbr != "░", f"wall {(x, y)} bordering floor renders as the void glyph"


def test_station_no_dangling_stubs(station):
    stubs = [p for p, c in station if isinstance(c, Wall) and c.abbr in set("╶╴╷╵")]
    assert not stubs, f"dangling single-direction wall stubs at {stubs[:5]}"


def test_station_renders_one_char_per_cell(station):
    for line in station.text_drawing.splitlines():
        assert len(line) == station.bounds.XX


def test_unknown_room_kind_rejected():
    with pytest.raises(ValueError):
        generate_station(room_kind="stadium")
