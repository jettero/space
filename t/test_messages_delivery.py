# coding: utf-8

import pytest
from space.msg import ReceivesMessages, Actors, Sound, SAY
from space.living.behavior import VL
from space.shell.list import Shell as ListShell


def test_simple_and_targeted_delivery(a_map, objs):
    objs.me.shell = ListShell()
    objs.dig_dug.shell = ListShell()

    objs.me.do("open door; sSW6s3w; look")
    assert len(objs.me.shell.msgs) == 6  # open door, move, look,map, look,map
    assert len(objs.dig_dug.shell.msgs) == 4  # open, move, look, look

    objs.me.simple_action("$N $vwave.")
    assert len(objs.me.shell.msgs) == 7
    assert len(objs.dig_dug.shell.msgs) == 5
    assert objs.me.shell.msgs[-1] == "You wave."
    assert objs.dig_dug.shell.msgs[-1] == "Paul waves."


def listen(o):
    for x in (o.me, o.dig_dug, o.stupid):
        x.shell = ListShell()
    return o


@pytest.fixture
def closed(objs):
    return listen(objs)


@pytest.fixture
def opened(objs):
    objs.me.do("open door")
    return listen(objs)


def test_hv_calc_sound_off(closed):
    assert closed.me.hv_calc(Actors(closed.me, None)) == ({closed.me}, set(), set())


def test_hv_calc_closed_door(closed):
    normal, neutral, muffled = closed.me.hv_calc(Actors(closed.me, None), sound=SAY)
    assert normal == {closed.me}
    assert not neutral
    assert muffled == {closed.dig_dug}


def test_hv_calc_open_door(opened):
    normal, neutral, muffled = opened.me.hv_calc(Actors(opened.me, None), sound=SAY)
    assert opened.dig_dug in normal
    assert opened.dig_dug not in neutral | muffled


def test_hv_calc_disjoint_tiers(closed):
    normal, neutral, muffled = closed.dig_dug.hv_calc(Actors(closed.dig_dug, None), sound=Sound("test", range=8))
    assert normal == {closed.dig_dug}
    assert neutral == {closed.stupid}
    assert muffled == {closed.me}


def test_normal_see_and_hear_once(opened):
    opened.me.do("say hi")
    assert opened.dig_dug.shell.msgs == ['Paul says, "Hi."']


def test_neutral_say(closed):
    closed.dig_dug.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", range=8))
    assert closed.stupid.shell.msgs == ['Someone says, "Hi."']


def test_neutral_later_mention(closed):
    closed.dig_dug.simple_action("$N $vstick out $p tongue.", sound=Sound("test", range=8))
    assert closed.stupid.shell.msgs == ["Someone sticks out their tongue."]


def test_neutral_through_door(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", distinct=0.25))
    assert closed.dig_dug.shell.msgs == ['Someone says, "Hi."']


def test_muffled_say(closed):
    closed.me.do("say hi")
    assert closed.dig_dug.shell.msgs == ["You hear muffled sounds."]
    closed.dig_dug.do("say hi")
    assert closed.me.shell.msgs[-1] == "You hear muffled sounds."


def test_muffled_custom(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", muffled_msg="$N $vhear a thump."))
    assert closed.dig_dug.shell.msgs == ["You hear a thump."]


def test_nothing_without_sound(closed):
    closed.me.simple_action("$N $vwave.")
    assert closed.dig_dug.shell.msgs == []


def test_nothing_below_min_hearability(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", min_hearability=0.35))
    assert closed.dig_dug.shell.msgs == []


def test_nothing_out_of_range(closed):
    closed.dig_dug.do("say hi")
    assert closed.stupid.shell.msgs == []


def test_voiceline_through_door(closed):
    closed.dig_dug.voiceline_frequency = True
    closed.dig_dug.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert closed.me.shell.msgs == ["You hear muffled sounds."]


def test_voiceline_kw(closed):
    closed.dig_dug.voiceline_frequency = True
    closed.dig_dug.voicelines = [VL("$N $vhum.", kw=dict(sound=Sound("hum", muffled_msg="$N $vhear humming.")))]
    closed.dig_dug.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert closed.me.shell.msgs == ["You hear humming."]


def test_sound_repr():
    assert repr(Sound("test", range=8)) == "Sound('test', range=8, min_hearability=0.1, distinct=0.6)"


def test_actor_gets_one_line(closed):
    closed.me.do("say hi")
    assert closed.me.shell.msgs == ['You say, "Hi."']


def test_targeted_sound_target_once(opened):
    opened.dig_dug.targeted_action("$N $vpoke $t.", opened.me, sound=SAY)
    assert opened.me.shell.msgs == ["Dig Dug pokes you."]
    assert opened.dig_dug.shell.msgs == ["You poke Paul."]


def test_other_action_skips_actor(opened):
    opened.me.other_action("$N $vwave.")
    assert opened.me.shell.msgs == []
    assert opened.dig_dug.shell.msgs == ["Paul waves."]
