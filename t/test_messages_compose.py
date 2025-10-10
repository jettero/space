# coding: utf-8

import pytest
from space.living.msg import Messages


def _compose(me, targ, msg, *obs):
    return Messages(
        me.compose(me, msg, [me, targ], *obs),
        me.compose(targ, msg, [me, targ], *obs),
        me.compose(None, msg, [me, targ], *obs),
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

@pytest.mark.parametrize(
    "msgs",
    [
        ("$N $vdie.", "You die.", "Paul dies."),
        ("$N $vare very cool.", "You are very cool.", "Paul is very cool."),
        ("$N $vhave $o.", "You have a bauble.", "Paul has a bauble."),
        ('$N $vdo "things" to $o.', 'You do "things" to a bauble.', 'Paul does "things" to a bauble.'),
    ],
)
def test_action_verb_agreement(objs, msgs):
    try:
        to_parse, us, them, other = msgs
    except ValueError:
        to_parse, us, them = msgs
        other = them

    msg = _compose(objs.me, objs.stupid, to_parse, objs.ubi)

    assert msg.us == us
    assert msg.them == them
    assert msg.them == other
