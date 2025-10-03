# coding: utf-8

from space.container import Container


class Sack(Container):
    class Meta(Container.Meta):
        mass = 0.1
        volume = 0.25
        mass_capacity = 5
        volume_capacity = 5
