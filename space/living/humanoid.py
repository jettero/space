# coding: utf-8

import logging
from collections import OrderedDict

import space.exceptions as E
from .base import Living
from .behavior import PointLessVoiceLines, VL
from .gender import Male, Female, Unknown
from .slots import Slots as BaseSlots, BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot, PackSlot
from ..door import Door
from ..msg import Sound, SAY
from ..stdobj import StdObj
from ..pfilter import adj_map

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
        ok, ctx = super().can_get_obj(obj)
        if not ok:
            return ok, ctx
        for h in (self.slots.right_hand_slot, self.slots.left_hand_slot):
            try:
                if h.accept(obj):
                    return True, {"obj": obj}
            except E.ContainerError:
                pass
        return False, {"error": f"It's not possible to get {obj}."}

    def do_get_obj(self, obj):
        eff = None
        for hand in (self.slots.right_hand_slot, self.slots.left_hand_slot):
            try:
                if hand.accept(obj):
                    hand.add_item(obj)
                    self.simple_action("$N $vget $o.", obj)
                    return
            except E.ContainerError as e:
                if eff is None:
                    eff = e
        if eff is not None:
            raise eff

    def can_open_obj(self, obj: Door):
        ok, ctx = obj.can_open()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, {"obj": obj}
            return False, {"error": f"{obj} is too far away"}
        return ok, ctx

    def do_open_obj(self, obj: Door):
        log.debug("do_open_obj(%s)", obj)
        self.changes_view(obj.do_open)
        self.simple_action("$N $vopen $o.", obj)

    @adj_map(obj="word")
    def can_open_word_obj(self, word: str, obj: Door):
        # the parser and obj.parse_match do consider 'word' as adjectives of
        # obj and filter the obj choices appropriately (thanks to @adj_map). So
        # if word is 'south' and there's a door to the south, then we can be
        # pretty sure we've selected the right door.

        return self.can_open_obj(obj)

    do_open_word_obj = do_open_obj

    def can_close_obj(self, obj: Door):
        ok, ctx = obj.can_close()
        if ok:
            if self.unit_distance_to(obj) <= self.reach:
                return ok, {"obj": obj}
            return False, {"error": f"{obj} is too far away"}
        if (reason := ctx.get("reason")) == "already-closed":
            return False, {"error": f"{obj} is already closed"}
        if reason == "stuck":
            return False, {"error": f"{obj} appears to be stuck"}
        if reason == "blocked":
            by = ctx["by"]
            return False, {"error": f"You're in the way of {obj}" if by is self else f"{by} is in the way of {obj}"}
        return False, {"error": f"You cannot close {obj}"}

    @adj_map(obj="word")
    def can_close_word_obj(self, word: str, obj: Door):
        return self.can_close_obj(obj)

    def do_close_obj(self, obj: Door):
        log.debug("do_close_obj(%s)", obj)
        self.changes_view(obj.do_close)
        self.simple_action("$N $vclose $o.", obj)

    do_close_word_obj = do_close_obj


class Human(PointLessVoiceLines, Humanoid):
    s = l = "human"
    d = "a human"

    def __init__(self, proper_name=None, short=None, **kw):
        super().__init__(proper_name=proper_name, short=short, **kw)

    voicelines = [
        VL('$N $vsay, "Hi there!"', sound=SAY),
    ]


class Skeleton(PointLessVoiceLines, Humanoid):
    s = l = "skeleton"
    a = "s"
    d = "a skeleton"

    def __init__(self, long=None, short=None, **kw):
        super().__init__(long=long, short=short, **kw)

    voicelines = [
        VL("$N $vgnash $p teeth in impotent rage.", sound=Sound("gnash", spl=20)),
    ]

    class Choices(Living.Choices):
        gender = (Unknown,)
