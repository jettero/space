#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import sys

from space.map.room import Room
from space.shell import ReadlineShell
from space.living import Human
from space.map.generate import generate as generate_map
from space.item import Ubi

from t.troom import a_map, o

c = sys.argv[1:]
if c[0:2] in (["get", "bauble"], ["bauble"], ["ubi"]):
    c = ["open door; sSW6s2w; get bauble"]
else:
    c = ["look"]

ReadlineShell(owner=o.me, init=c).loop()
