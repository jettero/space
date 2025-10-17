# coding: utf-8

import pytest
import inspect
import itertools
from space.living.msg import Messages, capitalize
from space.living import gender as gender_mod


def _compose(subj, targ, msg, *obs):
    return Messages(
        subj.compose(subj, msg, [subj, targ], *obs),
        subj.compose(targ, msg, [subj, targ], *obs),
        subj.compose(None, msg, [subj, targ], *obs),
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


def test_repeated_subject_tokens_basic(objs):
    msg = _compose(objs.me, objs.dig_dug, "$N $vare cool and $n $vare loud.")
    assert msg.us == "You are cool and you are loud."
    assert msg.them == f"{objs.dig_dug.a_short} is cool and {objs.dig_dug.subjective} is loud."
    assert msg.other == f"{objs.dig_dug.a_short} is cool and {objs.dig_dug.subjective} is loud."


def test_repeated_subject_tokens_basic(objs):
    msg = _compose(objs.me, objs.dig_dug, "$N $vare cool and $n $vare loud.")
    assert msg.us == "You are cool and you are loud."
    assert msg.them == f"{objs.me.a_short} is cool and {objs.me.subjective} is loud."
    assert msg.other == f"{objs.me.a_short} is cool and {objs.me.subjective} is loud."


# sloppy tableized bullshit below.
C = capitalize
L = lambda x: x
T = {
    "$N": (lambda x, y, w: "You" if x == w else C(x.a_short), lambda x, y, w: "You" if x == w else C(x.subjective)),
    "$n": (lambda x, y, w: "you" if x == w else L(x.a_short), lambda x, y, w: "you" if x == w else L(x.subjective)),
    # "$P": (lambda x, y, w: "Your" if x == w else C(x.po), lambda x, y, w: "You" if x == w else C(x.subjective)),
    # "$P": (lambda x, y, w: "your" if x == w else L(x.a_short), lambda x, y, w: "you" if x == w else L(x.subjective)),
    # ("$P", "Your", "Your", "Paul's", "His"),
    # ("$R", "Yourself", "Yourself", "Paulself", "Himself"),
    # ("$p", "your", "your", "Paul's", "his"),
    # ("$r", "yourself", "yourself", "Paulself", "himself"),
}
K = list(T)


@pytest.mark.parametrize("lt", K)
@pytest.mark.parametrize("rt", K)
def test_repeated_subject_all_combos(objs, lt, rt):
    # Note on reflexivity ... when the subject and object of a sentence are the
    # same person we mark the pronoun with -self to indicate that.
    #
    # [subj==obj]: Paul slaps himself.
    # [subj!=obj]: Paul slaps him.
    #
    # There's no way in english to mark a propernoun with this property, so
    # what is $R when it occurs before any other tag mention for the slot??
    #
    # Well, realistically, $R should turn to $N if it occurs before any other
    # tag, but I also think it's an error to write "$R $vare funny." So I'd
    # prefer it comes out Paulself for fits and shiggles.

    # XXX: # permutations() isn't with replacement like with the parametrized
    # vars above to make it so uo==to, we'd have to use product((...),(...))
    # instead.  we really should test uo==to, where $t goes to $n1r, but
    # that'll have to be later
    for uo, to, oo in itertools.permutations((objs.me, objs.dig_dug, objs.stupid), 3):
        u, t, o = _compose(uo, to, f"{lt}/{rt}")

        assert u == f"{T[lt][0](uo, to, uo)}/{T[rt][1](uo, to, uo)}"
        assert t == f"{T[lt][0](uo, to, to)}/{T[rt][1](uo, to, to)}"
        assert o == f"{T[lt][0](uo, to, oo)}/{T[rt][1](uo, to, oo)}"
