#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import sys

from space.map.room import Room
from space.shell import ReadlineShell
from space.living import Human
from space.map.generate import generate as generate_map
from space.item import Ubi

from troom import a_map, o

c = sys.argv[1:]
if not c:
    c = ['look']

ReadlineShell(owner=o.me, init=c).loop()
