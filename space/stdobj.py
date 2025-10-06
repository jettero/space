#!/usr/bin/env python
# coding: utf-8

from .container import Containable
from .named import Named


class StdObj(Named, Containable):
    def __init__(self, **kw):
        super().__init__(**kw)  # MRO insures we call Named.__init__ and Containable.__init__

    def __str__(self):
        return self.long

    def __repr__(self):
        return f'{self.__class__.__name__}<{self.short}>'
