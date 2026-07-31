# coding: utf-8

from .base import MapObj, DDIRS
from .cell import Cell
from .blocked import BlockedCell


class Wall(MapObj):
    _override = None
    attenuation = 0.9  # hearability loss across the barrier
    conv = {
        "": "░",
        "C": "▪",
        "n": "╵",
        "s": "╷",
        "e": "╶",
        "w": "╴",
        "ns": "│",
        "ew": "─",
        "ne": "└",
        "se": "┌",
        "nw": "┘",
        "sw": "┐",
        "new": "┴",
        "sew": "┬",
        "nsw": "┤",
        "nse": "├",
        "nsew": "┼",
    }

    @property
    def useless(self):
        for d in DDIRS:
            if self.dtype(d, Cell):
                return False
        return True

    @property
    def wcode(self):
        r = ""
        ccnt = 0
        for d in "nsew":
            dc = self.mpos(d)
            if isinstance(dc, Wall) or (isinstance(dc, BlockedCell) and dc.has_door):
                check = "ns" if d in "ew" else "ew"
                for c in check:
                    if dc.dtype(c, Cell) or self.dtype(c, Cell):
                        r += d
                        break
            elif isinstance(dc, Cell):
                ccnt += 1
        if ccnt == 4:
            return "C"
        return r

    @property
    def dcode(self):
        if self.useless:
            return ""
        dirs = {d for d in ("ne", "nw", "se", "sw") if isinstance((n := self.mpos(d)), Wall) and not n.useless}
        fwd = {"ne", "sw"} & dirs
        bwd = {"nw", "se"} & dirs
        return "╳" if fwd and bwd else "╱" if fwd else "╲" if bwd else ""

    @property
    def abbr(self):
        if self._override is not None:
            return self._override
        if (wc := self.wcode) in ("", "n", "s", "e", "w") and (dg := self.dcode):
            return dg
        return self.conv[wc]

    @abbr.setter
    def abbr(self, v):
        self._override = v
