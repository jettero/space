# coding: utf-8

import logging
from .dn import DN
from .vv import VV

log = logging.getLogger(__name__)


class Mass(DN):
    class Meta:
        convert_on_set = True
        units = "kg"


class Length(DN):
    class Meta:
        convert_on_set = True
        units = "m"


class Volume(DN):
    class Meta:
        convert_on_set = True
        units = "m³"


class Size:
    def __init__(self, mass=None, height=None, width=None, depth=None, volume=None, **kw):
        super().__init__()  # ancestor init never takes kwargs

        self.mass = mass

        if volume is None:
            self.height = height
            self.width = width
            self.depth = depth
        else:
            self.volume = volume

    @classmethod
    def compute_cuboid_dimensions(cls, v):
        if isinstance(v, (tuple, VV)):
            h, w, d = v
        else:
            h = w = d = v ** (1 / 3.0)
        return [Length(i) for i in (h, w, d)]

    @property
    def volume(self):
        return Volume(self.height * self.width * self.depth)

    @volume.setter
    def volume(self, v):
        if v is None:
            return
        self.height, self.width, self.depth = self.compute_cuboid_dimensions(v)

    @property
    def size(self):
        return VV(self.mass, self.volume)

    def __repr__(self):
        return f"{self.__class__.__name__}<{str(self)}>"

    def __str__(self):
        return f"{self.mass:0.2fa}, {self.height:0.2fa} × {self.width:0.2fa} × {self.depth:0.2fa}"

    def __init_subclass__(cls, *a, **kw):
        super().__init_subclass__(*a, **kw)

        for aname in BLESSED_PROPERTIES:
            if not isinstance((ca := getattr(cls, aname, None)), property):
                sa = getattr(Size, aname, None)
                log.debug("size-blessing %s.%s to %s (vs %s)", cls, aname, sa, ca)
                sa.fset(cls, ca)
                setattr(cls, aname, sa)

        # be sure to also deal with the cursed properties
        if not isinstance((ca := getattr(cls, "volume", None)), property):
            s = Size(volume=ca)
            log.debug("size-uncursing %s.volume to %s*%s*%s (vs %s)", cls, s._height, s._width, s._depth, ca)
            cls._height = s._height
            cls._width = s._width
            cls._depth = s._depth
            setattr(cls, "volume", Size.volume)


BLESSED_PROPERTIES = {"weight"}


def define_dimensional_property(cls, aname, acls):
    a = f"_{aname}"
    z = acls(0)

    def _g(self):
        return getattr(self, a, z)

    def _s(self, v):
        if v is None:
            return
        if not isinstance(v, acls):
            v = z + v
        if v < 0:
            v = z
        log.debug("setting %s.%s = %s", self, a, v)
        return setattr(self, a, v)

    p = property(_g).setter(_s)
    setattr(cls, aname, p)
    BLESSED_PROPERTIES.add(aname)


define_dimensional_property(Size, "mass", Mass)
define_dimensional_property(Size, "height", Length)
define_dimensional_property(Size, "width", Length)
define_dimensional_property(Size, "depth", Length)

Size.weight = Size.mass
