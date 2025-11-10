#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import sys, cProfile, pstats

from t.troom import a_map, o
from space.master import MasterControlProgram as MCP

profile = False

c = sys.argv[1:]
if c[0:2] in (["get"], ["ubi"], ["get", "bauble"], ["bauble"], ["ubi"]):
    c = ["open door; sSW6s2w; get bauble"]
elif c[0:2] in (["lotsa", "say"], ["say", "alot"]):
    c = [f"say hiya{x}" for x in range(30)]
    c.append("/quit")
elif c[0:1] in (["fill"],):
    c = [
        "open door; sSW6s2w; get bauble; l; l; l; smile; grin; bow",
        *(f"say this is a thing I said (x={x})" for x in range(200)),
    ]
elif c[0:1] in (["profile"],):
    c = [f"say this is a thing I said (x={x})" for x in range(200)]
    c.append("/quit")
    profile = True
else:
    c = ["look"]

if profile:
    with cProfile.Profile() as pr:
        MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
    with open("profile.txt", "w") as f:
        pstats.Stats(pr, stream=f).sort_stats("cumulative").print_stats()
else:
    MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
