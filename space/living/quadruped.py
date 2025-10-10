# coding: utf-8

import logging

from .base import Living
from .slots import Slots, MouthSlot

log = logging.getLogger(__name__)


class Quadruped(Living):
    s = l = "quadruped"
    a = "q"
    d = "a quadruped"

    class Slots(Slots):
        class Meta:
            slots = {"mouth": MouthSlot}
            default = "mouth"

    def can_get_obj(self, obj):
        for targ in obj:
            dist = self.unit_distance_to(targ)
            if dist <= self.reach:
                if self.slots.mouth.accept(targ):
                    # do_get expects 'obj'; align return key
                    return True, {"obj": targ}
        return False, {"error": "There's nothing like that nearby."}

    def do_get(self, obj):
        self.slots.mouth.add_item(obj)
        self.simple_action("$N $vget $o.", obj)

    def can_drop_obj(self, obj):
        for targ in obj:
            loc = getattr(targ, "location", None)
            if loc is None:
                continue
            if loc is self.pack:
                return True, {"obj": targ}
            try:
                if loc.owner is self:
                    return True, {"obj": targ}
            except Exception:
                pass
        return False, {"error": "You aren't holding that."}

    def do_drop(self, obj):
        self.location.add_item(obj)
        self.simple_action("$N $vdrop $o.", obj)
