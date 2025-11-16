# coding: utf-8

from space.container import Container
from space.stdobj import StdObj


class Sack(Container, StdObj):
    mass = 0.1
    volume = 0.25
    mass_capacity = 5
    volume_capacity = 5
