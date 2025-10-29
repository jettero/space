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
        return f"{self.__class__.__name__}<{self.short}>"


    # NOTE: sodval is StdObj distance value.  it's meant to give us an idea of
    # the value of the object when parsing. The idea is to make matching
    # something specific like a Human more valuable than matching a Humanoid,
    # more valuable than matching a Living, more valuable than matching a
    # StdObj. Even though, strictly speaking, a Human is also a StdObj.
    sodval = 1
    def __init_subclass__(cls):
        cls.sodval = len([x for x in cls.__mro__ if issubclass(x, StdObj)])
