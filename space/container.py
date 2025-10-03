# coding: utf-8

from collections import deque

import space.exceptions as E
from .pv import INFINITY
from .size import Size
from .obj import baseobj


class Containable(Size, baseobj):
    a = "~"
    s = "obj"
    l = "containable object"

    def __init__(self, mass=None, volume=None):
        Size.__init__(self, mass=mass, volume=volume)
        baseobj.__init__(self)


class CapacityMeta:
    class Meta:
        pass

    class Capacity(Size):
        class Meta:
            mass = INFINITY
            volume = INFINITY

    def __init_subclass__(cls):
        super().__init_subclass__()
        m = type(
            "Meta",
            (cls.Capacity.Meta,),
            {
                "mass": getattr(cls.Meta, "mass_capacity", cls.Capacity.Meta.mass),
                "volume": getattr(cls.Meta, "volume_capacity", cls.Capacity.Meta.volume),
            },
        )
        cls.Capacity = type("Capacity", (cls.Capacity,), {"Meta": m})


class Container(Containable, CapacityMeta):
    a = "~"
    l = s = "container"
    accept_types = tuple()

    class Meta:
        mass_capacity = INFINITY
        volume_capacity = INFINITY

    def __init__(self, *items, mass_capacity=None, volume_capacity=None, mass=None, volume=None):
        Containable.__init__(self, mass=mass, volume=volume)
        self._capacity = self.Capacity(mass=mass_capacity, volume=volume_capacity)
        self._items = deque()
        self.add_items(*items)

    @property
    def content_size(self):
        start = self.size * 0
        return sum([x.size for x in self._items], start)

    @property
    def capacity(self):
        return self._capacity.size

    @property
    def remaining_capacity(self):
        return self.capacity - self.content_size

    def add_items(self, *items):
        items = [i for i in items if self.accept(i)]
        for i in items:
            self._add_item(i)

    def _add_item(self, item):
        if item.location:
            item.location.remove_item(item)
        self._items.append(item)
        item.location = self

    def add_item(self, item):
        if self.accept(item):
            self._add_item(item)

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
