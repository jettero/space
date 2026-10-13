# coding: utf-8

import re
import pytest
import inspect
import itertools
from space.msg import Messages, Actors, capitalize
from space.living import gender as gender_mod
from space.verb.emote.soul import SOUL


@pytest.fixture
def opened(objs):
    objs.me.do("open door; sSWss")
    objs.stupid.do("sseee")


def test_opened_everyone_sees_everyone(objs, opened):
    livings = (objs.me, objs.dig_dug, objs.stupid)
    blind = [(a.s, b.s) for a in livings for b in (*livings, objs.ubi) if a is not b and not a.can_see(b)]
    pos = {x.s: x.location.pos for x in (*livings, objs.ubi)}
    assert not blind, f"{blind}\n{pos}\n{objs.me.location.map.text_drawing()}"


def _compose(subj, targ, msg, *obs):
    return Messages(
        subj.compose(subj, msg, [subj, targ], *obs),
        subj.compose(targ, msg, [subj, targ], *obs),
        subj.compose(None, msg, [subj, targ], *obs),
    )


def test_compose_listener_sees_name(me, dd):
    assert me.compose(dd, "$N $vwave.", Actors(me, None)) == "Paul waves."


@pytest.mark.parametrize(
    "msg, expect",
    [
        ("$N $vwave.", "Someone waves."),
        ("$N $vstick out $p tongue.", "Someone sticks out their tongue."),
        ("$N $vpat $r.", "Someone pats themself."),
        ("$P tongue wags.", "Someone's tongue wags."),
        ("$R wags.", "Someone-self wags."),
        ("$N $vpoke $no.", "Someone pokes them."),
    ],
)
def test_compose_listener_cannot_see(objs, msg, expect):
    assert objs.me.compose(objs.dig_dug, msg, Actors(objs.me, None)) == expect


def test_compose_unseen_object(objs):
    assert objs.me.compose(objs.me, "$N $vget $o.", Actors(objs.me, None), objs.ubi) == "You get something."


def test_compose_narrator_sees_all(objs):
    assert objs.me.compose(None, "$N $vget $o.", Actors(objs.me, None), objs.ubi) == "Paul gets a bauble."


def test_compose_you_beats_visibility(objs):
    assert objs.dig_dug.compose(objs.me, "$N $vpoke $t.", Actors(objs.dig_dug, objs.me)) == "Someone pokes you."


@pytest.mark.parametrize("GCls", [gender_mod.Not, gender_mod.GenderNeutral])
def test_they_takes_plural_verb(objs, GCls):
    objs.me.gender = GCls()
    msg = "$N $vare cool, $n $vhave fun, and $n $vwave."
    assert objs.me.compose(None, msg, Actors(objs.me, None)) == "Paul is cool, they have fun, and they wave."


def test_hidden_they_takes_plural_verb(objs):
    msg = "$N $vare cool, $n $vhave fun, and $n $vwave."
    assert objs.me.compose(objs.dig_dug, msg, Actors(objs.me, None)) == "Someone is cool, they have fun, and they wave."


@pytest.mark.usefixtures("opened")
@pytest.mark.parametrize(
    "msg, us, them, other",
    [
        (
            "$N $vpoint out that $t $v1have been trolled.",
            "You point out that Dig Dug has been trolled.",
            "Paul points out that you have been trolled.",
            "Paul points out that Dig Dug has been trolled.",
        ),
        (
            "$N $vnotice that $ts $v1need sleep badly, and $vsuggest $ts go to bed.",
            "You notice that Dig Dug needs sleep badly, and suggest she go to bed.",
            "Paul notices that you need sleep badly, and suggests you go to bed.",
            "Paul notices that Dig Dug needs sleep badly, and suggests she go to bed.",
        ),
        (
            "$N $vflash $t. $T1s $v1are impressed.",
            "You flash Dig Dug. She is impressed.",
            "Paul flashes you. You are impressed.",
            "Paul flashes Dig Dug. She is impressed.",
        ),
        (
            "$N1 $v1have gone $o-dead.",
            "Dig Dug has gone brain-dead.",
            "You have gone brain-dead.",
            "Dig Dug has gone brain-dead.",
        ),
    ],
)
def test_indexed_verb(objs, msg, us, them, other):
    assert _compose(objs.me, objs.dig_dug, msg, "brain") == (us, them, other)


SOUL_V1 = sorted(
    {
        t
        for patterns in SOUL["emotes"].values()
        for ts in patterns.values()
        for t in ([ts] if isinstance(ts, str) else ts)
        if re.search(r"\$v\d", t)
    }
)


@pytest.mark.usefixtures("opened")
@pytest.mark.parametrize("msg", SOUL_V1)
def test_soul_indexed_verbs(objs, msg):
    for line in _compose(objs.me, objs.dig_dug, msg, "brain"):
        assert not re.search(r"\b\d[a-z]", line), line
        assert "$" not in line, line


@pytest.mark.usefixtures("opened")
def test_bare_name(objs):
    assert _compose(objs.me, objs.dig_dug, "$M1, meet $M.") == ("Dig Dug, meet Paul.",) * 3
    assert _compose(objs.stupid, objs.me, "$M1, meet $M.") == ("Paul, meet Skellyman.",) * 3


@pytest.mark.usefixtures("opened")
def test_manager_rant(objs):
    msg = SOUL["emotes"]["themanagerrant"][""]
    for line in _compose(objs.me, None, msg):
        assert line.startswith('%^CYAN%^The Manager says%^RESET%^, "Paul, I hear')


@pytest.mark.usefixtures("opened")
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
@pytest.mark.usefixtures("opened")
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
        expect_other = f"{capitalize(s.a_short)} pats {s.reflexive} on {s.possessive} head."
        assert msg.other == expect_other


@pytest.mark.usefixtures("opened")
def test_reflexive_and_possessive_with_target(objs):
    triplets = itertools.permutations((objs.me, objs.dig_dug, objs.stupid), 3)

    for a, b, _c in triplets:
        msg = _compose(a, b, "$N $vsee $t pat $tr on $tp head.")

        assert msg.us == f"You see {b.a_short} pat {b.reflexive} on {b.possessive} head."
        assert msg.them == f"{capitalize(a.a_short)} sees you pat yourself on your head."
        assert msg.other == f"{capitalize(a.a_short)} sees {b.a_short} pat {b.reflexive} on {b.possessive} head."


def test_repeated_subject_tokens_basic(objs):
    msg = _compose(objs.me, objs.dig_dug, "$N $vare cool and $n $vare loud.")
    assert msg.us == "You are cool and you are loud."
    assert msg.them == f"{objs.dig_dug.a_short} is cool and {objs.dig_dug.subjective} is loud."
    assert msg.other == f"{objs.dig_dug.a_short} is cool and {objs.dig_dug.subjective} is loud."


@pytest.mark.usefixtures("opened")
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
@pytest.mark.usefixtures("opened")
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
