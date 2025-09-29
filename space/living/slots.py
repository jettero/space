# coding: utf-8

import re
import logging
from ..container import Slot, Container

log = logging.getLogger(__name__)
PROP_NAME_RE = re.compile(r'[^\w\d]+')

class PackSlot(Slot):
    accept_types = (Container,)

class BeltSlot(PackSlot):
    # accept_types = (Belt,)
    pass

class HandSlot(Slot):
    # accept StdObj by default so hands can hold items
    from ..stdobj import StdObj as _StdObj
    accept_types = (_StdObj,)
    del _StdObj

class LegsSlot(Slot):
    # accept_types = (LegsWearable,)
    pass

class TorsoSlot(Slot):
    # accept_types = (TorsoWearable,)
    pass

class HeadSlot(Slot):
    # accept_types = (HeadWearable,)
    pass

class FeetSlot(Slot):
    # accept_types = (FeetWearable,)
    pass


class Slots:
    class Meta:
        slots = {'left hand': HandSlot, 'right hand': HandSlot, 'pack': PackSlot}
        default = 'pack'

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._slots = sd = dict()
        def _p(priv_prop_name):
            def _g(self):
                log.debug('get %s.%s.item', self, priv_prop_name)
                return getattr(self, priv_prop_name).item
            def _s(self, v):
                getattr(self, priv_prop_name).item = v
            return property(_g).setter(_s)
        def_set = False
        for slot_name, slot_class in cls.Meta.slots.items():
            prop_name = PROP_NAME_RE.sub('_', slot_name)
            priv_prop_name = '_' + prop_name
            log.debug('[subclass] slot_name=%s prop_name=%s priv_prop_name=%s',
                slot_name, prop_name, priv_prop_name)
            sd[priv_prop_name] = (slot_name, slot_class)
            prop = _p(priv_prop_name)
            setattr(cls, prop_name, prop)
            if cls.Meta.default in (slot_name, prop_name, priv_prop_name):
                cls.default = prop
                def_set = True
        if not def_set:
            raise Exception(f'[subclass] unable to set default slot property {cls.Meta.default}')

    def __init__(self, owner):
        for priv_prop_name,a in self._slots.items():
            slot_name, slot_class = a
            setattr(self, priv_prop_name, slot_class(slot_name, owner))

    def __iter__(self):
        for priv_prop_name in self._slots:
            yield getattr(self, priv_prop_name)

    @property
    def inventory(self):
        items = []
        for slot in self:
            try:
                for it in slot:
                    items.append(it)
                    try:
                        for inner in it:
                            items.append(inner)
                    except Exception:
                        pass
            except Exception:
                pass
        return items
