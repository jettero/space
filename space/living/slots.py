# coding: utf-8

import re
import logging
from collections import OrderedDict
import space.exceptions as E
from ..container import Slot, Container
from ..stdobj import StdObj

log = logging.getLogger(__name__)
PROP_NAME_RE = re.compile(r"[^\w\d]+")


class HeadWearable:
    "just a placeholder"


class Belt:
    "just a placeholder"


class TorsoWearable:
    "just a placeholder"


class LegsWearable:
    "just a placeholder"


class FeetWearable:
    "just a placeholder"


class PackSlot(Slot):
    accept_types = (Container,)


class BeltSlot(PackSlot):
    accept_types = (Belt,)


class HandSlot(Slot):
    accept_types = (StdObj,)


class MouthSlot(HandSlot):
    pass


class LegsSlot(Slot):
    accept_types = (LegsWearable,)


class TorsoSlot(Slot):
    accept_types = (TorsoWearable,)


class HeadSlot(Slot):
    accept_types = (HeadWearable,)


class FeetSlot(Slot):
    accept_types = (FeetWearable,)


class Slots:
    class Meta:
        slots = OrderedDict()
        default = None

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._slots = sd = OrderedDict()

        def _p(slot_prop_name):
            def _g(self):
                log.debug("get %s.%s.item", self, slot_prop_name)
                return getattr(self, slot_prop_name).item

            def _s(self, v):
                getattr(self, slot_prop_name).item = v

            return property(_g).setter(_s)

        if cls.Meta.slots:
            def_set = False
            for slot_name, slot_class in cls.Meta.slots.items():
                prop_name = PROP_NAME_RE.sub("_", slot_name)
                slot_prop_name = prop_name + "_slot"
                log.debug(
                    "[subclass] slot_name=%s prop_name=%s slot_prop_name=%s", slot_name, prop_name, slot_prop_name
                )
                sd[slot_prop_name] = (slot_name, slot_class)
                prop = _p(slot_prop_name)
                setattr(cls, prop_name, prop)
                if cls.Meta.default in (slot_name, prop_name, slot_prop_name):
                    cls.default = prop
                    def_set = True
            if not def_set:
                raise E.LivingSlotSetupError(f"[subclass] unable to set default slot property {cls.Meta.default}")

    def __init__(self, owner):
        for slot_prop_name, a in self._slots.items():
            slot_name, slot_class = a
            setattr(self, slot_prop_name, slot_class(slot_name, owner))

    def __iter__(self):
        for slot_prop_name in self._slots:
            yield getattr(self, slot_prop_name)

    @property
    def inventory(self):
        items = []
        for slot in self:
            try:
                for it in slot:
                    items.append(it)
                    if isinstance(it, Container):
                        try:
                            for inner in it:
                                items.append(inner)
                        except AttributeError:
                            pass
            except AttributeError:
                pass
        return items
