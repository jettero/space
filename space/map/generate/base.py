# coding: utf-8

from ...roll import roll

def sparse(sparseness='1d10+3', start=1.0):
    if isinstance(sparseness, str):
        sparseness = roll(sparseness)
    if sparseness > start:
        sparseness = start - (sparseness/100.0)
    return sparseness
