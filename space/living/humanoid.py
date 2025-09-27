# coding: utf-8

import logging
import space.exceptions as E

from .base import Living
from .gender import Male, Female
from .slots import BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot
from ..door import Door

log = logging.getLogger(__name__)

class Humanoid(Living):
    s = l = 'humanoid'
    a = 'p'
    d = 'a humanoid'

    def can_open_obj(self, obj:Door):
        # XXX: how far can a humanoid reach and still interact with things? we need a better way to deal with this
        # use 1.42 as "adjacent"
        if self.unit_distance_to(obj) <= 1.42:
            return obj.can_open()
        return False, {'error': "What door?"}

    def do_open_obj(self, obj):
        obj.do_open()

    class Slots(Living.Slots):
        class Meta(Living.Slots.Meta):
            slots = Living.Slots.Meta.slots.copy()
            slots.update({
                'belt':       BeltSlot,
                'left-hand':  HandSlot,
                'right-hand': HandSlot,
                'legs':       LegsSlot,
                'torso':      TorsoSlot,
                'head':       HeadSlot,
                'feet':       FeetSlot,
            })

    class Choices(Living.Choices):
        gender = (Male, Female,)

    def can_close_obj(self, obj):
        if not isinstance(obj, Door):
            return False, {'reason': 'not-a-door'}
        return obj.can_close()

    def do_close_obj(self, obj):
        obj.do_close()

class Human(Humanoid):
    s = l = 'human'
    d = 'a human'
