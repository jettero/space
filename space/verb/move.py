# coding: utf-8

import logging

from .base import Verb
from ..map.dir_util import move_string_to_dirs, is_direction_string

log = logging.getLogger(__name__)

class Action(Verb):
    name = 'move'
    form = [
        'verb words',
        'verb OBJ words',
    ]

    def preprocess_tokens(self, me, **tokens):
        tokens = super().preprocess_tokens(me, **tokens)
        if 'moves' in tokens:
            moves = ' '.join( tokens['moves'] )
            if is_direction_string(moves):
                tokens['moves'] = tuple(move_string_to_dirs(moves))
            else:
                del tokens['moves']
        return tokens
