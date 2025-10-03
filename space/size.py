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


class SizeMeta:
    class Meta:
        pass

    @classmethod
    def compute_hwd(cls, v):
        raise NotImplementedError()

    def __init_subclass__(cls):
        super().__init_subclass__()
        cls._mass = Mass(getattr(cls.Meta, "mass", 0))
        vol = getattr(cls.Meta, "volume", None)
        if vol is not None:
            cls._height, cls._width, cls._depth = cls.compute_hwd(vol)
        else:
            cls._height = Length(getattr(cls.Meta, "height", 0))
            cls._width = Length(getattr(cls.Meta, "width", 0))
            cls._depth = Length(getattr(cls.Meta, "depth", 0))


class Size(SizeMeta):
    mass = height = width = depth = 0

    class Meta:
        mass = height = width = depth = 0

    def __init__(self, mass=None, height=None, width=None, depth=None, volume=None):
        super().__init__()
        self.mass = mass
        self.height = height
        self.width = width
        self.depth = depth
        self.volume = volume

    @property
    def volume(self):
        return Volume(self.height * self.width * self.depth)

    @classmethod
    def compute_hwd(cls, v):
        if isinstance(v, (tuple, VV)):
            h, w, d = v
        else:
            h = w = d = v ** (1 / 3.0)
        return [Length(i) for i in (h, w, d)]

    @volume.setter
    def volume(self, v):
        if v is None:
            return
        self.height = self.width = self.depth = self.compute_hwd(v)

    @property
    def size(self):
        return VV(self.mass, self.volume)

    def __repr__(self):
        return f"{self.__class__.__name__}<{str(self)}>"

    def __str__(self):
        return f"{self.mass:0.2fa}, {self.height:0.2fa} × {self.width:0.2fa} × {self.depth:0.2fa}"


def define_dimensional_property(cls, aname, acls):
    a = f"_{aname}"
    z = acls(0)

    def _g(self):
        return getattr(self, a)

    def _s(self, v):
        if v is None:
            return
        if not isinstance(v, acls):
            v = z + v
        return setattr(self, a, max(z, v))

    p = property(_g).setter(_s)
    setattr(cls, aname, p)


define_dimensional_property(Size, "mass", Mass)
define_dimensional_property(Size, "height", Length)
define_dimensional_property(Size, "width", Length)
define_dimensional_property(Size, "depth", Length)

Size.weight = Size.mass  # spurious without an acceleration field, but whatever
