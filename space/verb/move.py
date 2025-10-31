# coding: utf-8

import logging

from .base import Verb
from ..map.dir_util import move_string_to_dirs, is_direction_string

log = logging.getLogger(__name__)


class Action(Verb):
    name = "move"
    nick = ["mv"]

    def preprocess_tokens(self, me, **tokens):
        tokens = super().preprocess_tokens(me, **tokens)

        if moves := tokens.get("moves"):
            if isinstance(moves, tuple) and all(isinstance(x, str) for x in moves):
                moves = " ".join(moves)
                if is_direction_string(moves):
                    tokens["moves"] = moves2 = tuple(move_string_to_dirs(moves))
                    log.debug("preprocess_tokens(%s) -> %s", repr(moves), repr(moves2))
        return tokens
