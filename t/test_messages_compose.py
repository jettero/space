# coding: utf-8

import pytest
from space.living.msg import Actors

def test_compose_basic_pronouns_and_verb(objs):
    msg = objs.me.compose(objs.me, "$N $vattack $t.", [objs.me, objs.stupid])
    assert isinstance(msg, str)
    assert msg == f"You attack {objs.stupid.a_short}."

    others = objs.me.compose(None, "$N $vattack $t.", [objs.me, objs.stupid])
    assert others == f"{objs.me.a_short} attacks {objs.stupid.a_short}."


def test_compose_objects_variants(a_map, objs):
    who = [objs.me, objs.stupid]
    obs = [objs.ubi]
    msg_t = objs.me.compose(objs.me, "$N $vlook at $o.", who, *obs)
    assert msg_t == f"You look at {objs.ubi.a_short}."
    msg_t = objs.me.compose(None, "$N $vlook at $o.", who, *obs)
    assert msg_t == f"{objs.me.a_short} looks at {objs.ubi.a_short}."


def test_compose_vare_agreement(objs):
    msg = objs.me.action(Actors(objs.me, objs.stupid), "$N $vare very cool.")

    assert msg.us == "You are very cool."
    assert msg.them == "Paul is very cool."
    assert msg.other == "Paul is very cool."
