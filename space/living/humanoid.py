# coding: utf-8

from .base import Living
from .gender import Male, Female
from .slots import BeltSlot, HandSlot, LegsSlot, TorsoSlot, HeadSlot, FeetSlot

class Humanoid(Living):
    s = l = 'humanoid'
    a = 'p'
    d = 'a humanoid'

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
