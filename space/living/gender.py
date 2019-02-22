# coding: utf-8

from ..named import Named

class Gender(Named):
    a = 'U'
    s = 'unknown'
    l = 'Reproductive Modality'

class Male(Gender):
    a = 'M'
    s = 'male'

class Female(Gender):
    a = 'F'
    s = 'female'

class Other(Gender):
    a = 'O'
    s = 'other'

class Unknown(Gender):
    a = 'U'
    s = 'unknown'

class Not(Gender):
    a = 'N'
    s = 'not applicable'
