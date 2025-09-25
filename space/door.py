#!/usr/bin/env python
# coding: utf-8

from .obj import baseobj

class Door(baseobj):
    s = 'door'
    a = '+'

    # Basic open-state flags used by both objects and map cells.
    open: bool = False
    locked: bool = False
    stuck: bool = False

    def __init__(self, *items, open=False, locked=False, stuck=False, **kw):
        super().__init__(*items, **kw)
        self.open = bool(open)
        self.locked = bool(locked)
        self.stuck = bool(stuck)

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
