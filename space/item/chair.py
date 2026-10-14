# coding: utf-8

from space.stdobj import StdObj


class Chair(StdObj):
    a = "~"
    s = "chair"
    l = "chair"
    mass = 7
    volume = 0.25


class HeavyChair(Chair):
    l = "big heavy chair"
    mass = 80
    volume = 1
