# coding: utf-8

import logging
import space.exceptions as E

from .slots import Slots
from .base import Living
from .gender import Male, Female
from .slots import BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot
from ..door import Door

log = logging.getLogger(__name__)

class Humanoid(Living):
    s = l = 'humanoid'
    a = 'p'
    d = 'a humanoid'

    class Slots(Slots):
        slots = OrderedDict([
            ('head', HeadSlot),
            ('torso', TorsoSlot),
            ('right hand', HandSlot),
            ('left hand', HandSlot),
            ('legs', LegsSlot),
            ('feet', FeetSlot),
            ('pack', PackSlot),
        ])
        default = 'pack'

    class Choices(Living.Choices):
        gender = (Male, Female,)

    def can_get_obj(self, obj):
        for targ in obj:
            dist = self.unit_distance_to(targ)
            if dist <= self.reach:
                hands = (self.slots.right_hand, self.slots.left_hand)
                if any(h.accept(targ) for h in hands):
                    return True, {'target': targ}
        return False, {'error': "There's nothing like that nearby."}

    def do_get(self, target):
        for hand in (self.slots.right_hand, self.slots.left_hand):
            hand.add_item(target)

    def can_drop_obj(self, obj):
        for targ in obj:
            loc = getattr(targ, 'location', None)
            if loc is None:
                continue
            if loc is self.pack:
                return True, {'target': targ}
            try:
                if loc.owner is self:
                    return True, {'target': targ}
            except Exception:
                pass
        return False, {'error': "You aren't holding that."}

    def do_drop(self, target):
        self.location.add_item(target)

    def can_open_obj(self, obj:Door):
        # check door interaction within reach
        ok,err = obj.can_open()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok,err
            else:
                return False, {'error': f'{obj} is too far away'}
        return False, {'error': "What door?"}

    def do_open_obj(self, obj:Door):
        log.debug("do_open_obj(%s)", obj)
        obj.do_open()

    def can_close_obj(self, obj:Door):
        # check door interaction within reach
        ok,err = obj.can_close()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok,err
            else:
                return False, {'error': f'{obj} is too far away'}
        return False, {'error': "What door?"}

    def do_close_obj(self, obj:Door):
        log.debug("do_sclose_obj(%s)", obj)
        obj.do_close()

class Human(Humanoid):
    s = l = 'human'
    d = 'a human'
