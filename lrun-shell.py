#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,unused-import,no-member

import sys
from t.troom import a_map, o
from space.master import MasterControlProgram as MCP

profile = False

GET_BAUBLE = ["open door; sSW6s2w; get bauble; 2NEnn"]

c = sys.argv[1:]
if c[0:2] in (["get"], ["ubi"], ["get", "bauble"], ["bauble"], ["ubi"]):
    c = GET_BAUBLE
elif c[0:2] in (["lotsa", "say"], ["say", "alot"]):
    c = [f"say hiya{x}" for x in range(30)]
    c.append("/quit")
elif c[0:1] in (["fill"],):
    c = [*GET_BAUBLE, "l; l; l; smile; grin; bow",
        *(f"say this is a thing I said (x={x})" for x in range(200)),
    ]
elif c[0:1] in (["profile"],):
    c = [f"say this is a thing I said (x={x})" for x in range(200)]
    c.append("/quit")
    profile = True
else:
    c = ["look"]

if profile:
    import os, cProfile, pstats

    with cProfile.Profile() as pr:
        MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
    with open("profile.txt", "w") as f:
        pstats.Stats(pr, stream=f).sort_stats("cumulative").print_stats()
    h = max(25, int(int(os.environ.get("LINES", 27)) * 0.8))
    os.execvp("head", f"head -n {h} profile.txt".split())
else:
    MCP().start_instance(type="local", username="jettero", map=a_map, body=o.me, init=c)
