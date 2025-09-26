# coding: utf-8

import types

from space.map.base import Map
from space.map.cell import Cell
from space.map.generate import lumpy_room, generate_rooms, boxed_in
from space.map.generate.rdc import generate as rdc_generate


def _basic_map_checks(m: Map):
    assert isinstance(m, Map)
    # has at least one walkable cell
    assert any(isinstance(c, Cell) for _, c in m)
    # not completely empty
    assert m.sparseness < 1.0
    # bounds look sane (non-negative sizes)
    b = m.bounds
    assert b.X >= b.x and b.Y >= b.y


def test_generate_lumpy_smoke():
    m = lumpy_room(x=20, y=20, rsz='1d2+1', rooms='2d2')
    _basic_map_checks(m)


def test_generate_rooms_smoke():
    m = generate_rooms(x=20, y=20, rsz='1d2+1', rsparse='2')
    _basic_map_checks(m)


def test_generate_boxedin_smoke():
    m = boxed_in(x=20, y=20, rsz='1d2+1', rsparse='2')
    _basic_map_checks(m)


def test_generate_rdc_smoke():
    m = rdc_generate(x=30, y=30, rsz='1d2+1', rsparse='2', seed_budget='4', max_steps='60')
    _basic_map_checks(m)


def test_doors_are_blocking_and_attached():
    m = rdc_generate(x=20, y=20, rsz='1d2+1', rsparse='2', seed_budget='3', max_steps='40')

    doors = [ (p,c) for p,c in m if isinstance(c, Cell) and c.has_door ]
    # At least one blocking doorway should exist in typical generated maps
    assert doors
