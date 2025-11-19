# coding: utf-8

from collections import deque

import space.exceptions as E
from .pv import INFINITY
from .size import Size, BLESSED_PROPERTIES
from .obj import baseobj, register_haver_recurse_by_owner, register_location_leaf
from .named import Named
from .serial import Serial


class Containable(Size, baseobj):
    a = "~"
    s = "obj"
    l = "containable object"

    def __init__(self, **kw):
        super().__init__(**kw)  # calls both Size and baseobj __init__ (well, baseobj doesn't have one, but it would)


# Note, this is used by all sorts of things you can't pick up (rooms, living
# slots, etc) If you want to make a pack or a thing you can pick up, you
# probably also want StdObj
class Container(baseobj):
    a = "~"
    l = s = "container"
    accept_types = tuple()

    class Capacity(Size):
        mass = INFINITY
        volume = INFINITY

    def __init__(self, *items, mass_capacity=None, volume_capacity=None, **kw):
        super().__init__(**kw)
        self.capacity = self.Capacity(mass=mass_capacity, volume=volume_capacity)
        self._items = deque()
        self.add_items(*items)

    def __init_subclass__(cls):
        super().__init_subclass__()
        super_blessed_attrs = [f"{aname}_capacity" for aname in BLESSED_PROPERTIES]
        if to_copy := [(x, getattr(cls, x)) for x in super_blessed_attrs if hasattr(cls, x)]:

            class Capacity(cls.Capacity): ...

            cls.Capacity = Capacity
            for name, val in to_copy:
                aname, _ = name.split("_")
                setattr(Capacity, aname, val)
            # have to invoke this manually since we added these after it ran. :-(
            Capacity.__init_subclass__()

    @property
    def content_size(self):
        return sum([x.size for x in self._items], self.capacity.size * 0)

    @property
    def remaining_capacity(self):
        return self.capacity.size - self.content_size

    def add_items(self, *items):
        for item in items:
            if self.accept(item):
                if item.location:
                    item.location.remove_item(item)
                self._items.append(item)
                item.location = self

    add_item = add_items

    def remove_item(self, item):
        if item in self._items:
            if item.location:
                item.location = None
            self._items.remove(item)

    def remove_items(self, *items):
        for item in items:
            self.remove_item(item)

    def __iter__(self):
        yield from self._items

    @property
    def items(self):
        return self._items

    def biggest_item(self, filt=None):
        if filt:
            filtered = [x for x in self._items if isinstance(x, filt)]
            if filtered:
                return max(filtered, key=lambda x: x.mass)
        if self._items:
            return max(self._items, key=lambda x: x.mass)

    def accept(self, item):
        if item is self:
            raise E.ContainerError(f"{item} cannot contain iteself")
        if not isinstance(item, Containable):
            raise E.ContainerError(f"{item} is not containable")
        if item in self._items:
            raise E.ContainerError(f"{item} is already in {self}")
        if (self.remaining_capacity - item.size) < 0:
            raise E.ContainerCapacityError(f"{item} won't fit in {self}")
        if self.accept_types and not isinstance(item, self.accept_types):
            raise E.ContainerTypeError(f"{item} is the wrong type")
        return True

    def __len__(self):
        return len(self._items)

    def __iter__(self):
        return iter(self._items)


class Slot(Container):
    def __init__(self, name, owner=None):
        super().__init__()
        self.s = self.l = f"{name} slot"
        if owner is not None:
            self.owner = owner

    @property
    def item(self):
        for item in self:
            return item

    @item.setter
    def item(self, v):
        for item in self:
            if self.owner:
                self.owner.receive_item(item)
            self.remove_item(item)
        self.add_item(v)

    def accept(self, item):
        if self._items:
            raise E.ContainerError(f"{self} is occupied by {self._items[0]}")
        return super().accept(item)


register_haver_recurse_by_owner(Slot)
register_location_leaf(Container)
