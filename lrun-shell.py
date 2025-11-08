#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import sys

from t.troom import a_map, o
from space.master import MasterControlProgram as MCP

c = sys.argv[1:]
if c[0:2] in (["get", "bauble"], ["bauble"], ["ubi"]):
    c = ["open door; sSW6s2w; get bauble"]
elif c[0:2] in (["lotsa", "say"], ["say", "alot"]):
    c = [f"say hiya{x}" for x in range(30)]
    c.append("/quit")
else:
    c = ["look"]

MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
