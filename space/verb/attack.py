# coding: utf-8

import logging
from .base import Verb

log = logging.getLogger(__name__)


class Action(Verb):
    name = "attack"
    nick = "attack kill hit lacerate".split()
