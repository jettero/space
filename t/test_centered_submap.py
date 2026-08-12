# coding: utf-8

import pytest

from space.map.base import MapView
from space.map.util import Bounds


def test_a_view_reads_the_map_at_absolute_positions(a_map):
    view = MapView(a_map, Bounds(3, 2, 11, 8), filter_cells=False)
    assert (view.bounds.XX, view.bounds.YY) == (9, 7)
    for j, row in enumerate(view.cells):
        for i, cell in enumerate(row):
            assert cell is a_map.get(3 + i, 2 + j)


def test_a_view_of_a_view_composes_its_offset(a_map):
    inner = MapView(MapView(a_map, Bounds(3, 2, 11, 8), filter_cells=False), Bounds(5, 4, 8, 6), filter_cells=False)
    assert (inner.bounds.XX, inner.bounds.YY) == (4, 3)
    for j, row in enumerate(inner.cells):
        for i, cell in enumerate(row):
            assert cell is a_map.get(5 + i, 4 + j)


def test_a_view_of_a_view_pads_past_the_inner_edge(a_map):
    outer = MapView(a_map, Bounds(3, 2, 6, 5), filter_cells=False)
    inner = MapView(outer, Bounds(5, 4, 9, 8), filter_cells=False)
    lines = inner.text_drawing.split("\n")
    assert len(lines) == 5
    assert {len(x) for x in lines} == {5}
    assert [row[2:] for row in inner.cells] == [[None] * 3] * 5
    assert [row[:2] for row in inner.cells[2:]] == [[None] * 2] * 3


@pytest.mark.parametrize("cols,rows", [(1, 1), (5, 3), (31, 9)])
def test_a_view_is_exactly_the_size_of_its_bounds(a_map, me, cols, rows):
    x, y = me.location.pos
    view = MapView(me.vmap, Bounds(x - cols // 2, y - rows // 2, x - cols // 2 + cols - 1, y - rows // 2 + rows - 1))
    lines = view.text_drawing.split("\n")
    assert len(lines) == rows
    assert {len(x) for x in lines} == {cols}
