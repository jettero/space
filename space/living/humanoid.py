# coding: utf-8

import logging
import space.exceptions as E
from collections import OrderedDict

from .base import Living
from .gender import Male, Female
from .slots import Slots, BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot, PackSlot
from ..door import Door
from ..stdobj import StdObj

log = logging.getLogger(__name__)


class Humanoid(Living):
    s = l = "humanoid"
    a = "p"
    d = "a humanoid"

    class Slots(Slots):
        class Meta:
            slots = OrderedDict(
                [
                    ("head", HeadSlot),
                    ("torso", TorsoSlot),
                    ("right hand", HandSlot),
                    ("left hand", HandSlot),
                    ("legs", LegsSlot),
                    ("feet", FeetSlot),
                    ("pack", PackSlot),
                ]
            )
            default = "right hand"

    class Choices(Living.Choices):
        gender = (
            Male,
            Female,
        )

    def can_get_obj(self, obj: StdObj):
        if obj.owner == self:
            return False, {"error": "You already have that"}
        if obj.owner:
            return False, {"error": f"{obj.owner} would probably object if you took that."}
        if self.unit_distance_to(obj) > self.reach:
            return False, {"error": "That seems too far away"}
        for h in (self.slots._right_hand, self.slots._left_hand):
            try:
                if h.accept(obj):
                    return True, {"target": obj}
            except E.ContainerError:
                pass
        return False, {"error": "It's not possible to get that."}

    def do_get(self, target):
        for hand in (self.slots._right_hand, self.slots._left_hand):
            try:
                if hand.accept(target):
                    hand.add_item(target)
                    return
            except E.ContainerError as e:
                pass
        raise e

    def can_drop_obj(self, obj: StdObj):
        if obj.owner != self:
            return False, {"error": "You don't have that."}
        return True, {"target": obj}

    def do_drop(self, target):
        self.location.add_item(target)

    def can_open_obj(self, obj: Door):
        # check door interaction within reach
        ok, err = obj.can_open()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, err
            else:
                return False, {"error": f"{obj} is too far away"}
        return False, {"error": "What door?"}

    def do_open_obj(self, obj: Door):
        log.debug("do_open_obj(%s)", obj)
        obj.do_open()

    def can_close_obj(self, obj: Door):
        # check door interaction within reach
        ok, err = obj.can_close()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, err
            else:
                return False, {"error": f"{obj} is too far away"}
        return False, {"error": "What door?"}

    def do_close_obj(self, obj: Door):
        log.debug("do_sclose_obj(%s)", obj)
        obj.do_close()


class Human(Humanoid):
    s = l = "human"
    d = "a human"
