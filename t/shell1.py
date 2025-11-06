#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import os, sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from t.troom import a_map, o
from space.master import MasterControlProgram as MCP

c = sys.argv[1:]
if c[0:2] in (["get", "bauble"], ["bauble"], ["ubi"]):
    c = ["open door; sSW6s2w; get bauble"]
else:
    c = ["look"]

MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
