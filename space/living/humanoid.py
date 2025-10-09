# coding: utf-8

import logging
from collections import OrderedDict

import space.exceptions as E
from .base import Living
from .gender import Male, Female
from .slots import Slots as BaseSlots, BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot, PackSlot
from ..door import Door
from ..stdobj import StdObj

log = logging.getLogger(__name__)


class Humanoid(Living):
    s = l = "humanoid"
    a = "p"
    d = "a humanoid"

    class Slots(BaseSlots):
        class Meta:
            slots = OrderedDict(
                [
                    ("head", HeadSlot),
                    ("torso", TorsoSlot),
                    ("right hand", HandSlot),
                    ("left hand", HandSlot),
                    ("belt", BeltSlot),
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
            return False, {"error": f"You already have {obj}"}
        if obj.owner:
            return False, {"error": f"{obj.owner} would probably object if you took that."}
        if self.unit_distance_to(obj) > self.reach:
            return False, {"error": f"{obj} seems too far away"}
        for h in (self.slots.right_hand_slot, self.slots.left_hand_slot):
            try:
                if h.accept(obj):
                    return True, {"target": obj}
            except E.ContainerError:
                pass
        return False, {"error": f"It's not possible to get {obj}."}

    def do_get(self, target):
        eff = None
        for hand in (self.slots.right_hand_slot, self.slots.left_hand_slot):
            try:
                if hand.accept(target):
                    hand.add_item(target)
                    return
            except E.ContainerError as e:
                if eff is None:
                    eff = e
        if eff is not None:
            raise eff

    def can_drop_obj(self, obj: StdObj):
        if obj.owner != self:
            return False, {"error": f"You don't have {obj}."}
        return True, {"target": obj}

    def do_drop(self, target):
        self.location.add_item(target)

    def can_open_obj(self, obj: Door):
        ok, err = obj.can_open()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, err
            return False, {"error": f"{obj} is too far away"}
        return ok, err

    def do_open_obj(self, obj: Door):
        log.debug("do_open_obj(%s)", obj)
        obj.do_open()

    def can_close_obj(self, obj: Door):
        ok, err = obj.can_close()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, err
            return False, {"error": f"{obj} is too far away"}
        return ok, err

    def do_close_obj(self, obj: Door):
        log.debug("do_sclose_obj(%s)", obj)
        obj.do_close()


class Human(Humanoid):
    s = l = "human"
    d = "a human"

    def __init__(self, proper_name=None, short=None, **kw):
        super().__init__(proper_name=proper_name, short=short, **kw)


class Skeleton(Humanoid):
    s = l = "skeleton"
    a = "s"
    d = "a skeleton"

    def __init__(self, long=None, short=None, **kw):
        super().__init__(long=long, short=short, **kw)


class HumanSkeleton(Skeleton):
    s = l = "skeleton"
    a = "s"
    d = "a human skeleton"
