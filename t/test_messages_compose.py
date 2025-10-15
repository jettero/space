# coding: utf-8

import pytest
import inspect
import itertools
from space.living.msg import Messages, capitalize
from space.living import gender as gender_mod


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


def _all_gender_classes():
    """Yield all concrete Gender subclasses defined in the module.
    This auto-discovers new genders so tests cover them without manual edits.
    """
    base = gender_mod.Gender
    for name, obj in inspect.getmembers(gender_mod):
        if not inspect.isclass(obj):
            continue
        if not issubclass(obj, base):
            continue
        if obj is base:
            continue
        yield obj


@pytest.mark.parametrize("GCls", list(_all_gender_classes()))
def test_pronouns_in_messages(GCls, objs):
    g = GCls()
    objs.dig_dug.gender = g
    objs.stupid.gender = g

    msg = _compose(objs.dig_dug, objs.stupid, "$N $vpoke $t with $Np stick, then $N $vadmire $nr in the reflection.")

    assert msg.us.startswith("You poke ") and " with Your stick, then You admire yourself" in msg.us
    assert " you with " in msg.them.lower()
    assert msg.them.lower().endswith("self in the reflection.")
    assert objs.dig_dug.a_short in msg.other

    msg_t = _compose(objs.dig_dug, objs.stupid, "$t")
    msg_to = _compose(objs.dig_dug, objs.stupid, "$to")
    msg_n1o = _compose(objs.dig_dug, objs.stupid, "$n1o")
    assert msg_to.us == msg_n1o.us
    assert msg_to.them == msg_n1o.them
    assert msg_to.other == msg_n1o.other
    assert msg_t.them.lower() == msg_to.them.lower() == msg_n1o.them.lower() == "you"

    msg_poss = _compose(objs.dig_dug, objs.stupid, "$Np vs $n1p")
    assert msg_poss.us.startswith("Your vs ")
    assert " your" in msg_poss.them.lower()
    assert " vs " in msg_poss.other

    msg_np = _compose(objs.me, objs.stupid, "drop $np rock")
    msg_p = _compose(objs.me, objs.stupid, "drop $p rock")
    assert msg_np.us == "drop your rock"
    assert msg_p.us == msg_np.us
    assert msg_p.them == msg_np.them
    assert msg_p.other == msg_np.other


def test_reflexive_and_possessive_subject_only(objs):
    for s in (objs.me, objs.dig_dug, objs.stupid):
        msg = _compose(s, objs.stupid, "$N $vpat $r on $p head.")
        assert msg.us == "You pat yourself on your head."
        expect_other = f"{capitalize(s.short)} pats {s.reflexive} on {s.possessive} head."
        assert msg.other == expect_other


def test_reflexive_and_possessive_with_target(objs):
    triplets = itertools.permutations((objs.me, objs.dig_dug, objs.stupid), 3)

    for a, b, _c in triplets:
        msg = _compose(a, b, "$N $vsee $t pat $tr on $tp head.")

        assert msg.us == f"You see {b.a_short} pat {b.reflexive} on {b.possessive} head."
        assert msg.them == f"{capitalize(a.short)} sees you pat yourself on your head."
        assert msg.other == f"{capitalize(a.short)} sees {b.a_short} pat {b.reflexive} on {b.possessive} head."
