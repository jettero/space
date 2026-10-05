#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name,no-member

import sys
from pathlib import Path

from appserv import request

from t.troom import a_map, o
from space.master import MasterControlProgram as MCP
from space.map import import_map_from_path

for arg in sys.argv[1:]:
    if (candidate := Path(arg)).suffix == ".map" and candidate.is_file():
        a_map = import_map_from_path(candidate)
        for dood in o:
            a_map.randomly_drop(dood)
        break

MCP().start_instance(type="local", username=request["username"] or "guest", map=a_map, body=o.me, init=["look"])
