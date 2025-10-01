# coding: utf-8

import logging
import space.exceptions as E
from collections import OrderedDict

from .base import Living
from .gender import Male, Female
from .slots import Slots, BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot, PackSlot
from ..door import Door

log = logging.getLogger(__name__)

class Humanoid(Living):
    s = l = 'humanoid'
    a = 'p'
    d = 'a humanoid'

    class Slots(Slots):
        class Meta:
            slots = OrderedDict([
                ('head', HeadSlot),
                ('torso', TorsoSlot),
                ('right hand', HandSlot),
                ('left hand', HandSlot),
                ('legs', LegsSlot),
                ('feet', FeetSlot),
                ('pack', PackSlot),
            ])
            default = 'right hand'

    class Choices(Living.Choices):
        gender = (Male, Female,)

    def can_get_obj(self, obj):
        for targ in obj:
            dist = self.unit_distance_to(targ)
            log.debug('%s.can_get_obj() considering %s at a distance of %s', self, targ, dist)
            if dist <= self.reach:
                # the right_hand prop is effectively the contents of the right hand
                # the _right_hand prop is the actual slot, so we can invoke accept()
                hands = (self.slots._right_hand, self.slots._left_hand)
                for h in hands:
                    if h.accept(targ):
                        return True, {'target': targ}
        return False, {'error': "There's nothing like that nearby."}

    def do_get(self, target):
        for hand in (self.slots._right_hand, self.slots._left_hand):
            if hand.accept(target):
                hand.add_item(target)
                return

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
