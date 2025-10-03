#!/usr/bin/env python
# coding: utf-8

from .container import Containable
from .named import Named


class StdObj(Named, Containable):
    def __init__(self, **kw):
        super().__init__(**kw) # MRO insures we call Named.__init__ and Containable.__init__
