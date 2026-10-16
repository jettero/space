# coding: utf-8

import logging

import space.exceptions as E
from .base import Living
from .slots import Slots, MouthSlot
from ..stdobj import StdObj

log = logging.getLogger(__name__)


class Quadruped(Living):
    s = l = "quadruped"
    a = "q"
    d = "a quadruped"

    class Slots(Slots):
        class Meta:
            slots = {"mouth": MouthSlot}
            default = "mouth"

    def can_get_obj(self, obj: StdObj):
        ok, ctx = super().can_get_obj(obj)
        if not ok:
            return ok, ctx
        try:
            if self.slots.mouth_slot.accept(obj):
                return True, {"obj": obj}  # keys must match do_get_obj args
        except E.ContainerError:
            pass
        return False, {"error": f"It's not possible to get {obj}."}

    def do_get_obj(self, obj):
        self.slots.mouth_slot.add_item(obj)
        self.simple_action("$N $vget $o.", obj)
        self.location.map.time.charge(self, main=1)
