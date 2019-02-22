# coding: utf-8

from space.container import Containable

class Ubi(Containable):
    a = '$'
    s = 'bauble'
    l = 'useless bauble'

    class Meta:
        mass   = 0.1
        volume = 0.25
