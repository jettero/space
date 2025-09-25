# coding: utf-8

from .base import Living
from .gender import Male, Female
from .slots import BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot
from ..door import Door

class Humanoid(Living):
    s = l = 'humanoid'
    a = 'p'
    d = 'a humanoid'

    # Opening helpers; for now only Door is supported.
    def can_open_obj(self, obj:Door):
        if not isinstance(obj, Door):
            return False, {'reason': 'not-a-door'}
        return obj.can_open()

    def can_open_word_obj(self, word:str, obj:Door):
        ok, meta = self.can_open_obj(obj)
        if not ok and 'word' not in meta:
            meta = {**meta, 'word': word}
        return ok, meta

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

class Human(Humanoid):
    s = l = 'human'
    d = 'a human'
