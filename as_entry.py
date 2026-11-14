#!/usr/bin/env python
# coding: utf-8
# pylint: disable=invalid-name

import asyncio
import os
import signal
import time

from appserv import channel, request
from prompt_toolkit import prompt

from space import store
from space.living import Human
from space.map import import_map_from_path
from space.map.cell import Floor
from space.map.cell.blocked import Airlock, dock
from space.map.io import drop_floor_items, floor_items
from space.master import MCP
from space.serial import load
from space.util import same_program

STATION = "asset/station1.map"
SHIP = "asset/ship1.map"
QUIT = ("q", "quit", "exit")


def signup():
    print("No account here yet. Sign up with an ssh public key (^D quits).")
    while True:
        name = prompt("username: ", default=request["username"] or "").strip()
        key = prompt("ssh public key: ").strip()
        if not (name and key):
            print("both are required")
        elif "/" in name:
            print("no / in usernames")
        else:
            print("checking…")
            if not channel.user_exists(name):
                return channel.create_user(name, key=key).username
            print(f"{name} is taken")


def take_over(acct):
    """
    One login per account: SIGTERM the session that holds it (it saves and
    exits), wait for it to go, then record ours.
    """

    if (pid := (store.get("account", acct) or {}).get("pid")) and same_program(pid):
        print("closing your other session…")
        os.kill(pid, signal.SIGTERM)
        for _ in range(100):
            if not same_program(pid):
                break
            time.sleep(0.1)
        else:
            os.kill(pid, signal.SIGKILL)
    store.put("account", acct, {"pid": os.getpid()})


def pick(acct):
    while True:
        names = store.keys("character", f"{acct}/")
        for i, n in enumerate(names, 1):
            print(f"{i}) {n}")
        print("n) new character   q) quit")
        if (a := prompt("> ").strip().lower()) in QUIT:
            return None
        if a == "n":
            if not (name := prompt("name: ").strip()) or "/" in name or name in names:
                print("pick an unused name without /")
                continue
            return name
        if a.isdigit() and 0 < int(a) <= len(names):
            return names[int(a) - 1]


def play(acct, name):
    key = f"{acct}/{name}"
    station = import_map_from_path(STATION)
    ship_doc = store.get("ship", key) or {"map": SHIP, "items": {}}
    ship = import_map_from_path(ship_doc["map"])
    drop_floor_items(ship, ship_doc["items"])
    dock(station, ship)

    body = load(doc) if (doc := store.get("character", key)) else Human(name)
    body.active = True
    next(station.iter_cells(Airlock)).inner.neighbors(of_type=Floor)[0].add_item(body)

    def stop(*_):
        asyncio.get_running_loop().call_soon_threadsafe(body.shell.stop)

    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, stop)
    try:
        MCP.start_instance(type="local", username=acct, map=station, body=body, init=["look"])
    finally:
        for s in (signal.SIGTERM, signal.SIGHUP):
            signal.signal(s, signal.SIG_IGN)
        store.put("character", key, body.save())
        store.put("ship", key, {"map": ship_doc["map"], "items": floor_items(ship)})
        if store.get("account", acct) == {"pid": os.getpid()}:
            store.put("account", acct, {})


def main():
    acct = request["username"] if request["authenticated"] else signup()
    take_over(acct)
    if name := pick(acct):
        play(acct, name)


try:
    main()
except (EOFError, KeyboardInterrupt):
    pass
