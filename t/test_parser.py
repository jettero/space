# coding: utf-8

import logging
import pytest

from space.shell.list import Shell as ListShell
from space.living import Human
from space.map import Room
import space.parser as sp
from space.parser import parse, ExecutionPlan
from space.verb import VERBS

import space.exceptions as E

log = logging.getLogger(__name__)


@pytest.fixture
def room_and_people():
    room = Room()
    people = (Human("John Snow"), Human("Jaime Lannister"), Human("Jorah Mormont"))
    for dood in people:
        dood.shell = ListShell()
    for i, p in enumerate(people):
        room[2 + i, 3].add_item(p)
    return room, people


@pytest.fixture
def room(room_and_people):
    return room_and_people[0]


@pytest.fixture
def people(room_and_people):
    return room_and_people[1]


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
    me.do("look")
    xp = me.parse("attack jaime")
    assert xp
    assert xp.fn.__name__ == "do_attack_living"
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
    assert not xp

    xp = me.parse("look")
    assert xp

    xp = me.parse("look at things")
    assert bool(xp) is True


def test_pstate_nodes(me, room):
    xp = me.parse("")
    assert not xp


@pytest.mark.parametrize(
    "line,fn,kw",
    [
        ("look", "do_look", {}),
        ("say hi", "do_say_words", {"words": "hi"}),
        ("l", "do_look", {}),
        ("look at room", "do_look", {}),
        ("inventory", "do_inventory", {}),
        ("i", "do_inventory", {}),
        ("move s", "do_move_words", {"moves": ("s",)}),
    ],
)
def test_look_execution_plan(me, line, fn, kw):
    xp = me.parse(line)
    assert xp
    assert xp.fn.__name__ == fn
    assert xp.kw == kw
