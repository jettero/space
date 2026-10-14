#!/usr/bin/env python
# coding: utf-8

from .container import Containable
from .named import Named


class StdObj(Named, Containable):
    attached = False

    def __init__(self, **kw):
        super().__init__(**kw)  # MRO insures we call Named.__init__ and Containable.__init__

    def __str__(self):
        return self.long

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.short}>"

    def viewers(self) -> set:
        """
        The ReceivesMessages that can see this body (including itself).
        """

        from .msg import ReceivesMessages

        return {x for x in self.location.map.visicalc_submap(self).objects if isinstance(x, ReceivesMessages)}

    def changes_view(self, fn, *a):
        """
        Call fn(*a), then refresh_map() for everyone who could see this
        body before or after -- so anyone who lost sight redraws too.
        """

        before = self.viewers()
        fn(*a)
        for x in before | self.viewers():
            x.refresh_map()

    # NOTE: stdobj_dist_val is StdObj distance value.  it's meant to give us an idea of
    # the value of the object when parsing. The idea is to make matching
    # something specific like a Human more valuable than matching a Humanoid,
    # more valuable than matching a Living, more valuable than matching a
    # StdObj. Even though, strictly speaking, a Human is also a StdObj.
    stdobj_dist_val = 1

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls.stdobj_dist_val = len([x for x in cls.__mro__ if issubclass(x, StdObj)])
