# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest
from sroom import gen_sroom
from space.msg import WHISPER, SAY, SHOUT, DISTINCT
from space.shell.list import Shell as ListShell

W, S, H = "whisper psst", "say hi", "shout halp"
SOUNDS = {W: WHISPER, S: SAY, H: SHOUT}
WORDS = {W: 'Paul whispers, "Psst."', S: 'Paul says, "Hi."', H: 'Paul shouts, "Halp!"'}
SOMEONE = {W: 'Someone whispers, "Psst."', S: 'Someone says, "Hi."', H: 'Someone shouts, "Halp!"'}
UNHEARD = {W: "Paul whispers something.", S: "Paul says something.", H: "Paul shouts something."}
MUFFLED = {W: "You hear whispering.", S: "You hear muffled voices.", H: "You hear muffled shouting."}


@pytest.fixture
def sroom():
    def build(*a, **kw):
        a_map, o = gen_sroom(*a, **kw)
        o.dig_dug.shell = ListShell()
        return a_map, o

    return build


@pytest.fixture
def hear(sroom):
    def heard_by_dig_dug(cmd, *a, **kw):
        _, o = sroom(*a, **kw)
        o.me.do(cmd)
        return o.dig_dug.shell.msgs

    return heard_by_dig_dug


@pytest.fixture
def word_edge(sroom):
    def first_cell_below_distinct(sound):
        a_map, o = sroom(a=45)
        heard = a_map.hearicalc(o.me, spl=sound.spl)
        return next((x for x in range(2, 47) if heard.get((x, 1), 0) < DISTINCT), None)

    return first_cell_below_distinct


def rank(cmd, msgs):
    return [[], [MUFFLED[cmd]], [SOMEONE[cmd]]].index(msgs)


def test_falloff_per_cell(sroom):
    a_map, o = sroom(a=20)
    heard = a_map.hearicalc(o.me, spl=SAY.spl)
    levels = [heard[x, 1] for x in range(1, 22)]
    assert all(l1 > l2 for l1, l2 in zip(levels, levels[1:]))


@pytest.mark.parametrize("cmd", [W, S])
def test_seen_too_far(word_edge, hear, cmd):
    edge = word_edge(SOUNDS[cmd])
    assert edge and edge > 2
    assert hear(cmd, a=45, at=(edge - 1, 1)) == [WORDS[cmd]]
    assert hear(cmd, a=45, at=(edge, 1)) == [UNHEARD[cmd]]


@pytest.mark.parametrize(
    "cmd, far",
    [
        ("say hi!", "Paul exclaims something."),
        ("say hi?", "Paul asks something."),
        ("say hi :)", "Paul happily declares something."),
        ("say hi :P", "Paul sticks out his tongue and says something."),
        ("say (psst)", "Paul interjects something parenthetically."),
    ],
)
def test_say_variants_unheard(word_edge, hear, cmd, far):
    assert hear(cmd, a=45, at=(word_edge(SAY), 1)) == [far]


@pytest.mark.parametrize("cmd", [W, S])
def test_unseen_too_far(sroom, hear, cmd):
    a_map, o = sroom(a=2, b=70)
    heard = a_map.hearicalc(o.me, spl=SOUNDS[cmd].spl)
    seen = a_map.visicalc(o.me)
    leg = [(3, y) for y in range(1, 72) if (3, y) not in seen]
    far = next((p for p in leg if p not in heard), None)
    assert far and leg[0] != far
    assert rank(cmd, hear(cmd, a=2, b=70, at=leg[0])) > 0
    assert hear(cmd, a=2, b=70, at=far) == []


def test_corner_costs(sroom):
    l_map, lo = sroom(a=3, b=4)
    s_map, so = sroom(a=5)
    assert (4, 5) not in l_map.visicalc(lo.me)
    assert l_map.hearicalc(lo.me)[4, 5] < s_map.hearicalc(so.me)[6, 1]


@pytest.mark.parametrize(
    "cmd, barrier, expected",
    [
        (W, "D", None),
        (W, "W", None),
        (S, "D", MUFFLED),
        (S, "W", None),
        (H, "D", SOMEONE),
        (H, "W", MUFFLED),
    ],
)
def test_barriers(hear, cmd, barrier, expected):
    assert hear(cmd, barrier, a=2) == ([expected[cmd]] if expected else [])


@pytest.mark.parametrize("cmd", [W, S, H])
def test_open_door_is_floor(hear, cmd):
    assert hear(cmd, "O", a=2) == hear(cmd, a=2) == [WORDS[cmd]]


@pytest.mark.parametrize("cmd", [W, S, H])
def test_door_kinds(hear, cmd):
    ranks = [rank(cmd, hear(cmd, "D", a=2, attenuation=n)) for n in (20, 30, 50)]
    assert ranks == sorted(ranks, reverse=True)


def test_door_kinds_say(hear):
    assert hear(S, "D", a=2, attenuation=20) == [MUFFLED[S]]
    assert hear(S, "D", a=2, attenuation=50) == []


@pytest.mark.parametrize("cmd", [W, S, H])
def test_floor(sroom, cmd):
    a_map, o = sroom("D", a=2, b=10)
    assert min(a_map.hearicalc(o.me, min_propagation=10, spl=SOUNDS[cmd].spl).values()) >= 10
