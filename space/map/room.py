# coding: utf-8

from .cell import Cell, Floor, Wall
from .base import Map


class Room(Map):
    def __init__(self, *a):
        x, y = [i + 2 for i in self.atosz(a)]
        super().__init__(x, y)
        lx, ly, hx, hy = self.bounds
        for i in range(x):
            self[i, ly] = Wall()
            self[i, hy] = Wall()
        for j in range(1, hy):
            self[lx, j] = Wall()
            self[hx, j] = Wall()
        for i in range(1, hx):
            for j in range(1, hy):
                self[i, j] = Floor()
