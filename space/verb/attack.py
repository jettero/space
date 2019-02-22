# coding: utf-8

import logging
from .base import Verb

log = logging.getLogger(__name__)

class Action(Verb):
    name = 'attack'
    form = 'verb LIVING'
    nick = 'attack kill hit'.split()
