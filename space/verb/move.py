# coding: utf-8

import logging

from .base import Verb
from ..map.dir_util import move_string_to_dirs

log = logging.getLogger(__name__)

class Action(Verb):
    name = 'move'
    form = [
        'verb words',
        'verb OBJ words',
    ]

    def can(self, me, words, **kw):
        kw['words'] = words
        kw['moves'] = tuple( move_string_to_dirs(words) )
        return super().can(me, **kw)
