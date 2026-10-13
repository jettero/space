# coding: utf-8

"""Behavioral mixins for NPC/mob Livings.

PointLessVoiceLines emits occasional weighted voice lines during turns.
"""

import logging
import random
from ..roll import Chance
from ..msg import Sound

log = logging.getLogger(__name__)


class VL:
    """
    A voice line: msg is a "$N $v..." template, weight its relative odds
    of being picked, and sound how it carries (a space.msg.Sound such as
    SAY).  No sound means silent, sight-only.
    """

    def __init__(self, msg: str, weight: int = 1, sound: Sound | None = None):
        self.msg = msg
        self.weight = weight
        self.sound = sound

    def __repr__(self):
        return f"VL({self.msg!r}, {self.weight}, {self.sound})"


class PointLessVoiceLines:
    """Mixin that makes a mob occasionally emit silly voice lines.

    Attributes
    - voicelines: list of VL(msg, weight=1, sound=None); see VL.
      A bare string or plain tuple is promoted to a VL.
    - voiceline_frequency: space.roll.Chance("1d6=1")

    Conventions
    - If any super().do_receive(...) returns True, we consider the message handled
      and skip emitting a voice line.
    """

    voiceline_frequency = Chance("1d6=1")
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
        if vl := self._pick_weighted_voiceline():
            self.simple_action(vl.msg, sound=vl.sound)

    def _pick_weighted_voiceline(self):
        lines = []
        total = 0

        for it in self.voicelines:
            vl = it if isinstance(it, VL) else VL(it) if isinstance(it, str) else VL(*it)
            if vl.weight <= 0:
                continue
            lines.append(vl)
            total += vl.weight

        log.debug("_pick_weighted_voiceline() lines=%d total-line-weights=%d", len(lines), total)
        if total <= 0:
            return

        pick = random.randrange(total)
        cum = 0
        for vl in lines:
            cum += vl.weight
            if pick < cum:
                return vl
