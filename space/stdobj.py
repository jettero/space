#!/usr/bin/env python
# coding: utf-8

from .container import Containable
from .named import Named

class StdObj(Named, Containable):
    def __init__(self, short=None, abbr=None, long=None, mass=None, volume=None):
        Named.__init__(self, short=short, abbr=abbr, long=long)
        Containable.__init__(self, mass=mass, volume=volume)
