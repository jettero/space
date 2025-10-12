# coding: utf-8

"""Behavioral mixins for NPC/mob Lifings.

PointLessVoiceLines emits occasional weighted voice lines during turns.
"""

import logging
import random
from ..roll import Chance

log = logging.getLogger(__name__)


class PointLessVoiceLines:
    """Mixin that makes a mob occasionally emit silly voice lines.

    Attributes
    - voicelines: list of (message, weight) tuples. Message is a "$N $v..." string.
    - voiceline_frequency: Roll describing chance per turn (e.g., "1d10").

    Conventions
    - If any super().do_receive(...) returns True, we consider the message handled
      and skip emitting a voice line.
    """

    def __init__(self, voiceline_frequency="1d10", **kw):  # pylint: disable=unused-argument
        # Initialize behavior defaults before chaining.
        self.voiceline_frequency = Chance("1d10=1")
        self.voicelines = list()  # [(msg, weight), ...]
        super().__init__(**kw)

    def do_receive(self, msg, your_turn=False):  # pylint: disable=unused-argument
        if super().do_receive(msg, your_turn=your_turn):
            log.debug("do_receive() handled above")
            return True

        if not your_turn:
            return

        if not self.voiceline_frequency:
            log.debug("do_receive() it's not our time yet")
            return

        log.debug("do_receive() selecting voiceline")
        if line := self._pick_weighted_voiceline():
            self.simple_action(line)

    def _pick_weighted_voiceline(self):
        pairs = []
        total = 0

        for it in self.voicelines:
            if isinstance(it, str):
                msg, w = it, 1
            else:
                msg, w = it
            if w <= 0:
                continue
            pairs.append((msg, w))
            total += w

        if total <= 0:
            return

        pick = random.randrange(total)
        cum = 0
        for msg, w in pairs:
            cum += w
            if pick < cum:
                return msg
