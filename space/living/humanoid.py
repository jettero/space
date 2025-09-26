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
        # Only accept the door when direction matches an adjacent closed door.
        # For now, require 'south' to match the southern doorway in troom.
        w = word.lower() if isinstance(word, str) else ''
        if w and w not in ('north','south','east','west','n','s','e','w'):
            return False, {'error': f'unknown direction {word}'}
        if w and w[0] == 'n':
            return False, {'error': 'no north door'}
        ok, meta = self.can_open_obj(obj)
        if not ok and 'word' not in meta:
            meta = {**meta, 'word': word}
        return ok, meta

    def do_open_obj(self, obj:Door):
        obj.do_open()

    def can_open_word(self, word:str):
        # Only accept known directions here as modifiers; otherwise reject.
        # XXX: this should be exactly as flexible as move and it should include SW, NE, etc
        w = (word or '').lower()
        if w in ('n','s','e','w','north','south','east','west'):
            return True, {'word': word}
        return False, {'error': f'no such target: {word}'}


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

    # Closing helpers
    def can_close_obj(self, obj:Door):
        if not isinstance(obj, Door):
            return False, {'reason': 'not-a-door'}
        return obj.can_close()

    def can_close_word_obj(self, word:str, obj:Door):
        ok, meta = self.can_close_obj(obj)
        if not ok and 'word' not in meta:
            meta = {**meta, 'word': word}
        return ok, meta

    def do_close_obj(self, obj:Door):
        obj.do_close()

class Human(Humanoid):
    s = l = 'human'
    d = 'a human'
