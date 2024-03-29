# coding: utf-8

import logging

from .base import Verb
from ..map.dir_util import move_string_to_dirs, is_direction_string

log = logging.getLogger(__name__)

class Action(Verb):
    name = 'move'

    def preprocess_tokens(self, me, **tokens):
        tokens = super().preprocess_tokens(me, **tokens)
        if 'moves' in tokens:
            moves = ' '.join( tokens.pop('moves') )
            if is_direction_string(moves):
                tokens['moves'] = tuple(move_string_to_dirs(moves))
            log.debug('%s -> %s', moves, tokens.get('moves') )
        return tokens
