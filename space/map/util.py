# coding: utf-8

from ..size import Length
from ..vv import VV
from .cell import Cell, MapObj

def _check_cell(pos):
    if isinstance(pos, Cell):
        pos = VV(pos.pos)
    return VV(*pos)

def _check_cells(*pos):
    for i in pos:
        yield _check_cell(i)

class LineSeg:
    ''' adds properties to a two-tuple of points '''

    def __init__(self, pos1, pos2):
        self.pos1 = _check_cell(pos1)
        self.pos2 = _check_cell(pos2)
        self.diff = self.pos2 - self.pos1

    def __str__(self):
        return f'{self.pos1} → {self.pos2}'
    __repr__ = __str__

    @property
    def direction(self):
        return self.diff.direction

    @property
    def distance(self):
        return Length(Cell.Meta.width) * self.diff.length

    @property
    def center(self):
        dirv, mag = self.diff.dirmag
        return self.pos1 + (dirv * mag/2)

class Edges(tuple):
    ''' adds properties to a list/tuple of LineSegs '''

    def __new__(cls, *a):
        return super().__new__(cls, a)

    @property
    def centers(self):
        return tuple( e.center for e in self )

    def intersected_by(self, other):
        for e in self:
            if e.intersected_by( other ):
                return True
        return False

class Box:
    ''' adds properties to a position in order to describe (and compute it) as a box '''

    def __init__(self, pos):
        self.loc = pos = _check_cell(pos)
        self.loc = pos
        self.center = self.loc + 0.5
        self.ul = pos + (0,0)
        self.ur = pos + (1,0)
        self.lr = pos + (1,1)
        self.ll = pos + (0,1)
        self.edges = Edges(
            LineSeg(self.ul, self.ur), LineSeg(self.ur, self.lr),
            LineSeg(self.lr, self.ll), LineSeg(self.ll, self.ul) )

    def __repr__(self):
        return f'Box[{tuple(self.loc)}]'

    def intersected_by(self, other):
        return self.edges.intersected_by(other)

    def line_to(self, other):
        if not isinstance(other, Box):
            try: other = other.box
            except AttributeError:
                raise TypeError(f'{other} is not a box and lacks a .box property')
        return LineSeg(self.center, other.center)

MapObj.box = property(lambda x: Box(x.pos))

class Bounds:
    x = y = X = Y = None

    def __init__(self, *a):
        if not a or a[0] is None:
            return
        if len(a) == 4:
            self.x, self.y, self.X, self.Y = a
        elif len(a) == 1:
            cells = a[0].cells if hasattr(a[0], 'cells') else a[0]
            if cells and cells[0]:
                self.x = self.y = 0
                self.X = max([ len(row) for row in cells ]) - 1
                self.Y = len(cells) - 1
        else:
            raise ValueError('Bounds(cells) or Bounds(x,y,X,Y)')

    @property
    def XX(self):
        if None in (self.x, self.X):
            return 0
        return 1 + (self.X - self.x)

    @property
    def YY(self):
        if None in (self.y, self.Y):
            return 0
        return 1 + (self.Y - self.y)

    @property
    def xy_iter(self):
        for j in self.y_iter:
            for i in self.x_iter:
                yield (i,j)

    @property
    def y_iter(self):
        if self.y is None:
            return range(0,-1)
        return range(self.y, self.Y+1)

    @property
    def x_iter(self):
        if self.x is None:
            return range(0,-1)
        return range(self.x, self.X+1)

    def __getitem__(self, i):
        return tuple(self)[i]

    def __iter__(self):
        for i in 'xyXY':
            yield getattr(self, i)

    def __str__(self):
        return f'{self.XX}x{self.YY}'

    def __repr__(self):
        return f'Bounds(x={self.x}, y={self.y}, X={self.X}, Y={self.Y}, XX={self.XX}, YY={self.YY})'

    def _in(self, x,y):
        if x is not None and self.x is not None and self.x <= x <= self.X and self.y <= y <= self.Y:
            return True
        return False

    def contains(self, *a):
        if len(a) == 2:
            return self._in(*a)
        if isinstance(a[0], (list,tuple)) and len(a[0]) == 2:
            return self._in(*a[0])
        return False
