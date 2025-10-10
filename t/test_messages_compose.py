# coding: utf-8

import pytest
import inspect
from space.living.msg import Messages
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
        # Skip abstract/compat classes that are aliases via inheritance if any
        yield obj


@pytest.mark.parametrize("GCls", list(_all_gender_classes()))
def test_pronouns_in_messages(GCls, objs):
    # Assign both actor and target this gender and check token expansion
    g = GCls()
    objs.dig_dug.gender = g
    objs.stupid.gender = g

    # Exercise subjective ($N), objective ($t), possessive ($Np), reflexive ($Nr)
    # Use lowercase variants for others where capitalization differs.
    msg = _compose(objs.dig_dug, objs.stupid, "$N $vpoke $t with $Np stick, then $N $vadmire $nr in the reflection.")

    # Actor view (subjective for self -> You; target objective -> you/em/etc.; possessive -> Your; reflexive -> yourself)
    assert msg.us.startswith("You poke ") and " with Your stick, then You admire yourself" in msg.us

    # Target view (actor name third-person; target objective -> you)
    assert " you with " in msg.them.lower()
    # Reflexive refers to target (themself/emself/etc.)
    assert msg.them.lower().endswith("self in the reflection.")

    # Others view: third-person forms; reflexive of subject resolves via gender; target may be pronoun ($to)
    assert objs.dig_dug.a_short in msg.other

    # Parity: $to and $n1o should be identical (both objective pronouns); $t may differ (articles)
    msg_t   = _compose(objs.dig_dug, objs.stupid, "$t")
    msg_to  = _compose(objs.dig_dug, objs.stupid, "$to")
    msg_n1o = _compose(objs.dig_dug, objs.stupid, "$n1o")
    assert msg_to.us == msg_n1o.us
    assert msg_to.them == msg_n1o.them
    assert msg_to.other == msg_n1o.other
    # $t differs from pronoun tokens for non-recipient perspectives (uses a_short)
    assert msg_t.them.lower() == msg_to.them.lower() == msg_n1o.them.lower() == "you"

    # Possessives: $Np (actor possessive) vs $n1p (target possessive)
    msg_poss = _compose(objs.dig_dug, objs.stupid, "$Np vs $n1p")
    # Actor view: Your vs your
    assert msg_poss.us.startswith("Your vs ")
    # Target view: actor's possessive is name/Their/etc.; target possessive becomes your
    assert " your" in msg_poss.them.lower()
    # Others: both sides render third-person possessives without perspective shifts
    assert " vs " in msg_poss.other
