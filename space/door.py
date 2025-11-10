#!/usr/bin/env python
# coding: utf-8

from .stdobj import StdObj


class Door(StdObj):
    a = "+"
    s = l = "door"
    d = "a door"

    # Basic open-state flags used by both objects and map cells.
    open: bool = False
    locked: bool = False
    stuck: bool = False

    # Whether this door is attached to a cell (not portable/removable)
    attached: bool = False

    @property
    def abbr(self):
        return "□" if self.open else "■"

    def __init__(self, *items, is_open=False, is_locked=False, is_stuck=False, is_attached=False, **kw):
        super().__init__(*items, **kw)
        self.open = bool(is_open)
        self.locked = bool(is_locked)
        self.stuck = bool(is_stuck)
        self.attached = bool(is_attached)

    def can_open(self):
        if self.open:
            return False, {"error": f"{self} is already open"}
        if self.locked:
            return False, {"error": f"{self} is locked"}
        if self.stuck:
            return False, {"error": f"{self} appears to be stuck"}
        return True, {"target": self}  # keys must match do_open args

    def do_open(self):
        self.open = True
        if self.attached and (cell := self.location) and (m := cell.map):
            m.invalidate()

    def can_close(self):
        ok = self.open and not self.stuck
        meta = {}
        if not ok:
            if not self.open:
                meta["reason"] = "already-closed"
            elif self.stuck:
                meta["reason"] = "stuck"
        return ok, meta

    def do_close(self):
        self.open = False
        if self.attached and (cell := self.location) and (m := cell.map):
            m.invalidate()
