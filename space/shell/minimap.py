# coding: utf-8

import logging

from prompt_toolkit.formatted_text import ANSI
from prompt_toolkit.formatted_text.utils import to_formatted_text

from space.map.base import MapView
from space.map.util import Bounds

from .pane import clip_fragments, pad_fragments

log = logging.getLogger(__name__)


class Minimap:
    """
    The map band pinned to the top-right of the shell's message window.

    It owns no map of its own: it crops whatever view the shell last received
    (Shell.map_view) to the band with an ordinary bounded MapView, and asks
    the shell to draw it.  Nothing here computes perception -- the body
    already did that when it looked.

    rows() returns fragment rows exactly `width` columns wide (a one column
    gutter plus the drawing), or [] when folded away, ownerless, or before
    the first map has arrived.
    """

    max_frac = 0.4
    gap = 1

    def __init__(self, shell):
        self.shell = shell
        self.width = 0
        self.cache_key = None
        self.cache_map = None
        self.cache_rows = list()

    @property
    def visible(self):
        return self.shell.config["maps.minimap"]

    def rows(self, width: int, height: int) -> list:
        """
        Render the band for a width×height pane, memoized on size, position
        and which map we were given -- the drawing only changes when one of
        those does, so keystrokes cost nothing.
        """

        a_map = self.shell.map_view
        if not self.visible or self.shell.owner is None or a_map is None or width < 20 or height < 4:
            self.width = 0
            return []

        cols = max(1, int(width * self.max_frac) - self.gap)
        rows = max(1, int(height * self.max_frac))
        self.width = cols + self.gap

        if self.cache_key != (key := (cols, rows, tuple(self.shell.owner.location.pos))) or self.cache_map is not a_map:
            log.debug("Minimap.rows() render %dx%d at %s", cols, rows, key[2])
            self.cache_key, self.cache_map = key, a_map
            view = MapView(a_map, Bounds.centered(self.shell.owner.location.pos, cols, rows))
            self.cache_rows = [self.gutter(line) for line in self.shell.draw_map(view)]
        return self.cache_rows

    def gutter(self, line: str) -> list:
        """One drawing line, gutter-prefixed and sized to exactly self.width columns."""

        return pad_fragments(clip_fragments([("", " " * self.gap)] + to_formatted_text(ANSI(line)), self.width), self.width)
