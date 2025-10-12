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
    - voiceline_frequency: space.roll.Chance("1d6=1")

    Conventions
    - If any super().do_receive(...) returns True, we consider the message handled
      and skip emitting a voice line.
    """

    voiceline_frequency = Chance('1d6=1') 
    voicelines = list()

    def __init__(self, *a, voiceline_frequency=None, **kw):  # pylint: disable=unused-argument
        if isinstance(voiceline_frequency, str):
            self.voiceline_frequency = Chance(voiceline_frequency)
        elif isinstance(voiceline_frequency, Chance):
            self.voiceline_frequency = voiceline_frequency
        if self.voicelines is None:
            self.voicelines = list()
        if a:
            self.voicelines = list(a)
        super().__init__(*a, **kw)

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

        log.debug("_pick_weighted_voiceline() lines=%d total-line-weights=%d", len(pairs), total)
        if total <= 0:
            return

        pick = random.randrange(total)
        cum = 0
        for msg, w in pairs:
            cum += w
            if pick < cum:
                return msg
