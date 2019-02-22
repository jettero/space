# coding: utf-8

from collections import namedtuple

def nico(*a, **kw):
    for i in a:
        if isinstance(i, dict):
            kw.update(i)
    c = namedtuple('NickNameObject', kw.keys())
    return c(**kw)
