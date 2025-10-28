#!/usr/bin/env python
# coding: utf-8


def deep_eq(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in a.keys() | b.keys():          # union of keys
            va, vb = a.get(k, None), b.get(k, None)
            if not (va and vb):               # either side missing or falsy
                continue
            if not deep_eq(va, vb):
                return False
        return True
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(deep_eq(x, y) for x, y in zip(a, b))
    return a == b

