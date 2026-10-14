# coding: utf-8

import pytest
from space.msg import ReceivesMessages, Actors, Sound, SAY, SILENCE, WHISPER
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
    assert closed.me.hv_calc(Actors(closed.me, None)) == ({closed.me}, set(), set(), set())


def test_hv_calc_closed_door(closed):
    normal, unheard, neutral, muffled = closed.me.hv_calc(Actors(closed.me, None), sound=SAY)
    assert normal == {closed.me}
    assert not unheard
    assert not neutral
    assert muffled == {closed.dig_dug}


def test_hv_calc_open_door(opened):
    normal, unheard, neutral, muffled = opened.me.hv_calc(Actors(opened.me, None), sound=SAY)
    assert opened.dig_dug in normal
    assert opened.dig_dug not in unheard | neutral | muffled


def test_hv_calc_disjoint_tiers(closed):
    normal, unheard, neutral, muffled = closed.dig_dug.hv_calc(Actors(closed.dig_dug, None), sound=Sound("test"))
    assert normal == {closed.dig_dug}
    assert not unheard
    assert neutral == {closed.stupid}
    assert muffled == {closed.me}


def test_hv_calc_unheard(me, ss):
    normal, unheard, neutral, muffled = me.hv_calc(Actors(me, None), sound=WHISPER)
    assert ss in unheard
    assert ss not in normal | neutral | muffled


@pytest.mark.parametrize(
    "cmd, far",
    [
        ("whisper psst", "Paul whispers something."),
        ("shout halp", 'Paul shouts, "Halp!"'),
    ],
)
def test_seen_but_unheard(me, dd, ss, cmd, far):
    me.do(cmd)
    assert ss.shell.msgs == [far]
    assert dd.shell.msgs[-1].startswith("Paul") and '"' in dd.shell.msgs[-1]


def test_unheard_nonspeech_gets_normal(me, ss):
    me.simple_action("$N $vstomp.", sound=Sound("stomp"))
    assert ss.shell.msgs == ["Paul stomps."]


def test_silence(me, dd, ss):
    me.simple_action('$N $vmouth, "$O"', "hi.", sound=SILENCE.copy(unheard_msg="$N $vmouth something."))
    assert me.shell.msgs == ['You mouth, "Hi."']
    assert dd.shell.msgs == ss.shell.msgs == ["Paul mouths something."]


def test_sound_copy():
    s = SAY.copy(unheard_msg="$N $vmumble something.")
    assert (s.name, s.spl, s.muffled_msg) == (SAY.name, SAY.spl, SAY.muffled_msg)
    assert s.unheard_msg == "$N $vmumble something." != SAY.unheard_msg


def test_normal_see_and_hear_once(opened):
    opened.me.do("say hi")
    assert opened.dig_dug.shell.msgs == ['Paul says, "Hi."']


def test_neutral_say(closed):
    closed.dig_dug.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test"))
    assert closed.stupid.shell.msgs == ['Someone says, "Hi."']


def test_neutral_later_mention(closed):
    closed.dig_dug.simple_action("$N $vstick out $p tongue.", sound=Sound("test"))
    assert closed.stupid.shell.msgs == ["Someone sticks out their tongue."]


def test_neutral_through_door(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", spl=80))
    assert closed.dig_dug.shell.msgs == ['Someone says, "Hi."']


def test_muffled_say(closed):
    closed.me.do("say hi")
    assert closed.dig_dug.shell.msgs == ["You hear muffled voices."]
    closed.dig_dug.do("say hi")
    assert closed.me.shell.msgs[-1] == "You hear muffled voices."


def test_shout_through_door(closed):
    closed.me.do("shout halp")
    assert closed.dig_dug.shell.msgs == ['Someone shouts, "Halp!"']


def test_shout_out_of_say_range(closed):
    closed.dig_dug.do("shout halp")
    assert closed.stupid.shell.msgs == ['Someone shouts, "Halp!"']


def test_whisper_stops_at_door(closed):
    closed.me.do("whisper psst")
    assert closed.dig_dug.shell.msgs == []


def test_muffled_custom(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", muffled_msg="$N $vhear a thump."))
    assert closed.dig_dug.shell.msgs == ["You hear a thump."]


def test_nothing_without_sound(closed):
    closed.me.simple_action("$N $vwave.")
    assert closed.dig_dug.shell.msgs == []


def test_nothing_below_min_propagation(closed):
    closed.me.simple_action('$N $vsay, "$O"', "hi.", sound=Sound("test", spl=40))
    assert closed.dig_dug.shell.msgs == []


def test_voiceline_through_door(closed):
    closed.dig_dug.voiceline_frequency = True
    closed.dig_dug.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert closed.me.shell.msgs == ["You hear muffled voices."]


def test_voiceline_sound(closed):
    closed.dig_dug.voiceline_frequency = True
    closed.dig_dug.voicelines = [VL("$N $vhum.", sound=Sound("hum", muffled_msg="$N $vhear humming."))]
    closed.dig_dug.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert closed.me.shell.msgs == ["You hear humming."]


def test_vl_repr():
    assert repr(VL("$N $vhum.", sound=SAY)) == "VL('$N $vhum.', 1, Sound('say', spl=60))"


def test_sound_repr():
    assert repr(Sound("test", spl=40)) == "Sound('test', spl=40)"


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
