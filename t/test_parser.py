# coding: utf-8
# pylint: disable=invalid-name,redefined-outer-name,unused-argument

import logging
import pytest

from space.living import Human
from space.map import Room
import space.parser as sp
from space.verb import VERBS

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
    xp = me.parse("attack jaime")
    assert xp
    assert xp.fn.__name__ == "do_attack"
    assert xp.kw.get("target") == target


def test_attack_exec(me, target, room):
    hp1 = target.hp
    me.parse("attack jaime")()
    hp2 = target.hp
    assert hp2 < hp1


def test_move_parse(me, room):
    dt = {
        "n": "north North NORTH nOrth n".split(),
        "s": "south South s".split(),
        "e": "east East e".split(),
        "w": "west West w".split(),
    }
    room[7, 7] = me
    for d, sl in dt.items():
        for s in sl:
            xp = me.parse(f"move {s}")
            assert xp
            assert xp.kw.get("moves") == (d,)
            assert xp.fn.__name__ == "do_move_words"


def test_move(me, target, room):
    assert me.location.pos == (2, 3)
    me.parse("move north")()
    assert me.location.pos == (2, 2)
    me.parse("move east")()
    assert me.location.pos == (3, 2)
    xp = me.parse("move s")
    assert "is already there" in str(xp.error)
    with pytest.raises(E.ParseError):
        xp()
    assert me.location.pos == (3, 2)


def test_naked_dir_move_cmds(me, bystander, room):
    xp = me.parse("move 2sse")
    tsse = ("s", "s", "s", "e")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == tsse

    xp = me.parse("move shit")
    assert not xp
    assert xp.error

    xp = me.parse("2sse")
    assert xp
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == tsse

    tssep = tsse + ("n", "s", "e", "w")
    xp = me.parse("move 2sse nsew")
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == tssep

    xp = me.parse("2sse nsew")
    assert xp.fn.__name__ == "do_move_words"
    assert xp.kw.get("moves") == tssep


def test_extra_args_fail(me, room):
    xp = me.parse("move around stuff")
    assert bool(xp) is False
    assert "around" in xp.error
    assert "stuff" in xp.error

    xp = me.parse("look")
    assert bool(xp) is True

    xp = me.parse("look at things")
    assert bool(xp) is False
    assert "at" in xp.error
    assert "things" in xp.error


def test_pstate_nodes(me, room):
    xp = me.parse("")
    assert bool(xp) is False
    assert "unable to understand" in xp.error


def test_all_verbs_fname_contains_name(objs):
    # New parser doesn't expose PSNode/PState; emulate by ensuring verbs loaded
    sp.find_verb(False)
    assert VERBS, "expected find_verb/parse to construct all verbs by now"
    me = objs.me
    for name in VERBS.keys():
        xp = me.parse(name)
        if xp:
            assert name in xp.fn.__name__


@pytest.mark.parametrize(
    "vname",
    [name for name, v in VERBS.items()],
)
def test_all_verb_and_emote_names_parse_cleanly(objs, vname):
    assert "ambiguous" not in objs.me.parse(vname).error
