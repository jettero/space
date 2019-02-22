# coding: utf-8

from space.map import Cell, Room
from space.map import Map

def test_one_map():
    m = Map(21,23)
    assert len(m.cells) == 23
    for row in m.cells:
        assert len(row) == 21

def test_dirgets():
    r = Room(5,5)
    assert r[0,0].n is None
    assert r[0,0].w is None
    assert r[0,0].e is r[1,0]
    assert r[0,0].s is r[0,1]

    assert r[6,6].n is r[6,5]
    assert r[6,6].w is r[5,6]
    assert r[6,6].e is None
    assert r[6,6].s is None

def test_room():
    r = Room(10,10)
    assert len(r.cells) == 12
    for row in r.cells:
        assert len(row) == 12
        for c1,c2 in zip(row, row[1:-1]):
            assert c1.e == c2
            assert c2.w == c1

    for r1,r2 in zip(r.cells, r.cells[1:-1]):
        for c1,c2 in zip(r1, r2):
            assert c1.s == c2
            assert c2.n == c1

def test_assignments():
    r = Room(10,10)
    m = Map(2,2)
    m[5.5] = r
    assert m[5,5].s is m[5,6]
    m[5,5].n = Cell()
    m[5,5].w = Cell()
    assert m[4,5].e is m[5,5]
    assert m[5,4].s is m[5,5]
    assert m[5,5].n is m[5,4]
    assert m[5,5].w is m[4,5]

def test_indexing():
    r = Room(10,10)
    p = (3,3)
    c = r[p]
    assert c.pos == p
    assert r[c] == p

def test_complicated_map_coordinates():
    m = Map()
    m[9,0] = Room(3,3)
    m[4,0] = Room(5,5)
    m[0,6] = Room(5,5)
    m[8,6] = Room(5,5)

    id_set = set()
    for pos,cell in m:
        if cell is not None:
            assert cell.pos == pos
            assert m[pos] is cell
            assert id(cell) not in id_set
            id_set.add(id(cell))

    id_set = set()
    mc = max([ len(row) for row in m.cells ])
    mr = len(m.cells)
    for y in range(mr):
        for x in range(mc):
            c = m[x,y]
            if c is not None:
                assert m[x,y].pos == (x,y)
                assert id(c) not in id_set
                id_set.add(id(c))
