# coding: utf-8

import logging
from .base import Verb

log = logging.getLogger(__name__)

class Action(Verb):
    name = 'look'
    form = [
        'verb',
      # 'verb word',
      # 'verb "at" target',
    ]
