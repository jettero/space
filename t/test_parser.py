# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import logging
import pytest

from space.living import Human
from space.map import Room
import space.parser as sp

import space.exceptions as E

log = logging.getLogger(__name__)


@pytest.fixture
def people():
    return (Human("John Snow"), Human("Jaime Lannister"), Human("Jorah Mormont"))


@pytest.fixture
def room(people):
    r = Room()
    for i, p in enumerate(people):
        r[2 + i, 3].add_item(p)
    return r


@pytest.fixture
def me(people):
    return people[0]


@pytest.fixture
def target(people):
    return people[1]


@pytest.fixture
def bystander(people):
    return people[2]


def test_attack_parse(me, target, room):
    p = sp.Parser()
    pstate = p.parse(me, "attack jaime")
    assert pstate.winner.verb.name == "attack"
    assert pstate.winner.do_args.get("target") == target


def test_attack_exec(me, target, room):
    p = sp.Parser()
    hp1 = target.hp
    p.parse(me, "attack jaime")()
    hp2 = target.hp
    assert hp2 < hp1


def test_move_parse(me, room):
    p = sp.Parser()
    dt = {
        "n": "north North NORTH nOrth n".split(),
        "s": "south South s".split(),
        "e": "east East e".split(),
        "w": "west West w".split(),
    }
    room[7, 7] = me
    for d, sl in dt.items():
        for s in sl:
            pstate = p.parse(me, f"move {s}")
            assert bool(pstate)
            assert pstate.winner.do_args.get("moves") == (d,)
            assert pstate.winner.verb.name == "move"


def test_move(me, target, room):
    p = sp.Parser()
    assert me.location.pos == (2, 3)
    p.parse(me, "move north")()
    assert me.location.pos == (2, 2)
    p.parse(me, "move east")()
    assert me.location.pos == (3, 2)
    pstate = p.parse(me, "move s")
    assert "is already there" in str(pstate.error)
    with pytest.raises(E.ParseError):
        pstate()
    assert me.location.pos == (3, 2)


def test_naked_dir_move_cmds(me, bystander, room):
    p = sp.Parser()
    pstate = p.parse(me, "move 2sse")
    tsse = ("s", "s", "s", "e")
    assert pstate
    assert pstate.high_score_verb.name == "move"
    assert pstate.high_score_args.get("moves") == tsse

    pstate = p.parse(me, "move shit")
    assert not pstate
    assert pstate.high_score_verb.name == "move"
    assert pstate.high_score_args == None

    pstate = p.parse(me, "2sse")
    assert pstate
    assert pstate.high_score_verb.name == "move"
    assert pstate.high_score_args.get("moves") == tsse

    tssep = tsse + ("n", "s", "e", "w")
    pstate = p.parse(me, "move 2sse nsew")
    assert pstate.high_score_verb.name == "move"
    assert pstate.high_score_args.get("moves") == tssep

    pstate = p.parse(me, "2sse nsew")
    assert pstate.high_score_verb.name == "move"
    assert pstate.high_score_args.get("moves") == tssep


def test_extra_args_fail(me, room):
    p = sp.Parser()

    pstate = p.parse(me, "move around stuff")
    assert bool(pstate) is False
    assert "around" in pstate.error
    assert "stuff" in pstate.error

    pstate = p.parse(me, "look")
    assert bool(pstate) is True

    pstate = p.parse(me, "look at things")
    assert bool(pstate) is False
    assert "at" in pstate.error
    assert "things" in pstate.error


def test_pstate_nodes(me, room):
    p = sp.Parser()
    pstate = p.parse(me, "")

    # Empty input no longer matches verbs; ensure pstate reflects that.
    assert pstate.states is None
    assert bool(pstate) is False
    assert "unable to understand" in pstate.error


def test_all_verbs_fname_contains_name(objs):
    sp.find_verb(False)
    assert sp.VERBS, "expected find_verb/parse to construct all verbs by now"

    # Construct a PSNode chain via Parser.plan/evaluate by seeding PState
    # Use empty input to avoid leftover tokens from a bogus verb; then seed states.
    ps = sp.PState(objs.me, "")
    # Seed all verbs; PSNode expects positional verbs, not the verb dict
    ps.states = sp.PSNode(*sp.VERBS.values())
    # Ensure a fresh fill/plan and no extra tokens to mismatch rhints.
    ps.filled = False
    ps.tokens = []
    p = sp.Parser()
    p.plan(ps)
    p.evaluate(ps)

    for psn in ps.states:  # iterate all verbs and kids
        if psn.fname:
            assert psn.verb.name in psn.fname
