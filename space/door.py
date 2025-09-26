#!/usr/bin/env python
# coding: utf-8

from .stdobj import StdObj

class Door(StdObj):
    s = 'door'
    a = '+'

    # Basic open-state flags used by both objects and map cells.
    open: bool = False
    locked: bool = False
    stuck: bool = False

    # Whether this door is attached to a cell (not portable/removable)
    attached = False

    def __init__(self, *items, open=False, locked=False, stuck=False, attached=False, **kw):
        super().__init__(*items, **kw)
        self.open = bool(open)
        self.locked = bool(locked)
        self.stuck = bool(stuck)
        self.attached = bool(attached)

    def can_open(self):
        """Return (ok, meta) describing whether the door can be opened.

        Consumed by actors (e.g., Humanoid) and by map-cell wrappers.
        """
        ok = not self.open and not self.locked and not self.stuck
        meta = {}
        if not ok:
            if self.open:
                meta['reason'] = 'already-open'
            elif self.locked:
                meta['reason'] = 'locked'
            elif self.stuck:
                meta['reason'] = 'stuck'
        return ok, meta

    def do_open(self):
        self.open = True

    def can_close(self):
        """Return (ok, meta) for closing the door."""
        ok = self.open and not self.stuck
        meta = {}
        if not ok:
            if not self.open:
                meta['reason'] = 'already-closed'
            elif self.stuck:
                meta['reason'] = 'stuck'
        return ok, meta

    def do_close(self):
        self.open = False
