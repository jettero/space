# coding: utf-8

import pytest
from space.living.msg import Actors, Messages

def _compose(me, targ, msg):
    return Messages(
        me.compose(me, msg, [me, targ]),
        me.compose(targ, msg, [me, targ]),
        me.compose(None, msg, [me, targ]),
    )

def test_compose_basic_pronouns_and_verb(objs):
    msg = _compose(objs.me, objs.dig_dug, "$N $vattack $t.")
    assert msg.us == f"You attack {objs.dig_dug.a_short}."
    assert msg.them == f"{objs.me.a_short} attacks you."
    assert msg.other == f"{objs.me.a_short} attacks {objs.dig_dug.a_short}."

    msg = _compose(objs.me, objs.stupid, "$N $vattack $t.")
    assert msg.us == f"You attack {objs.stupid.a_short}."
    assert msg.them == f"{objs.me.a_short} attacks you."
    assert msg.other == f"{objs.me.a_short} attacks {objs.stupid.a_short}."


# def test_compose_objects_variants(a_map, objs):
#     who = [objs.me, objs.stupid]
#     obs = [objs.ubi]
#     msg_t = objs.me.compose(objs.me, "$N $vlook at $o.", who, *obs)
#     assert msg_t == f"You look at {objs.ubi.a_short}."
#     msg_t = objs.me.compose(None, "$N $vlook at $o.", who, *obs)
#     assert msg_t == f"{objs.me.a_short} looks at {objs.ubi.a_short}."


# @pytest.mark.parametrize(
#     "msgs",
#     [
#         ("$N $vdie.", "You die.", "Paul dies."),
#         ("$N $vare very cool.", "You are very cool.", "Paul is very cool."),
#         ("$N $vhave $o.", "You have a bauble.", "Paul has a bauble."),
#         ('$N $vdo "things" to $o.', 'You do "things" to a bauble.', 'Paul does "things" to a bauble.'),
#     ],
# )
# def test_action_verb_agreement(objs, msgs):
#     try:
#         to_parse, us, them, other = msgs
#     except ValueError:
#         to_parse, us, them = msgs
#         other = them

#     msg = objs.me.action(Actors(objs.me, objs.stupid), to_parse, objs.ubi)

#     assert msg.us == us
#     assert msg.them == them
#     assert msg.them == other
