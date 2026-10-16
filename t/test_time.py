# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest
from space.find import this_body
from space.shell.mob import Shell as MobShell


@pytest.fixture
def mobs(me, dd, ss, monkeypatch):
    for b, r in ((me, 20), (dd, 10), (ss, 1)):
        monkeypatch.setattr(b.initiative, "roll", lambda r=r: r)
    dd.shell = MobShell(owner=dd)
    ss.shell = MobShell(owner=ss)
    me.do("n")
    return me.location.map.time


@pytest.fixture
def fight(mobs, me, mcp):
    me.do("attack dig dug")
    mcp.run()
    return mobs


def test_my_turn_without_fight(me, dd):
    t = me.location.map.time
    assert t.my_turn(me, main=2, cells=12)[0]
    assert t.my_turn(dd, main=1)[0]


def test_attack_starts_fight(mobs, me, dd, mcp):
    hp = dd.hp
    me.do("attack dig dug")
    assert dd.hp == hp
    assert dd in me.aggro and me in dd.aggro
    assert mobs.fighting
    assert (me.shell.your_turn, (), {}) in mcp.queue
    assert not any("your turn" in m for m in me.shell.msgs)


def test_my_turn_in_fight(fight, me, dd):
    assert fight.my_turn(me)[0]
    assert fight.my_turn(dd) == (False, {"error": "It's not your turn."})
    assert "It's your turn (round 1): 2 main, 1 small." in me.shell.msgs


def test_six_cells_is_one_move_action(fight, me):
    assert me.do("6w")
    assert me.location.pos == (1, 4)
    assert fight.main == 1


def test_move_too_far(fight, me):
    assert me.do("n6w")
    assert me.location.pos == (1, 3)
    assert not me.do("6e")
    assert me.shell.msgs[-1] == "You can't move that far."
    assert me.location.pos == (1, 3)


def test_turn_handoff(fight, me, dd, mcp, monkeypatch):
    me.do("attack dig dug; attack dig dug")
    fight.charge(me, small=1)
    assert (dd.shell.your_turn, (), {}) in mcp.queue
    hp, seen = me.hp, []
    monkeypatch.setattr(dd, "attack", lambda t, f=dd.attack: seen.append(this_body()) or f(t))
    mcp.run()
    assert seen == [dd, dd]
    assert this_body() is None
    assert me.hp < hp
    assert fight.current is me and fight.round == 2


def test_fight_ends(fight, me, dd, mcp):
    dd.hurt(dd.hp - 1)
    me.do("attack dig dug")
    mcp.run()
    assert "The fight is over." in me.shell.msgs
    assert not fight.fighting
    assert fight.my_turn(dd)[0]


def test_pass_keeps_aggro(fight, me, dd, mcp):
    assert me.do("pass")
    assert fight.current is dd
    assert dd in me.aggro
    assert (dd.shell.your_turn, (), {}) in mcp.queue


def test_disengage(fight, me, dd, mcp):
    assert me.do("disengage")
    assert not me.aggro
    assert fight.fighting and fight.current is dd
    assert not me.do("calm down")
    assert dd.do("calm down")
    assert not dd.aggro
    mcp.run()
    assert "The fight is over." in me.shell.msgs
    assert not fight.fighting


def test_disengage_without_aggro(me):
    assert not me.do("disengage")
    assert me.shell.msgs[-1] == "You're not fighting anyone."


def test_mob_disengages_when_target_unseen(objs, a_map, mobs, me, dd, ss, mcp):
    a_map[8, 1] = dd
    objs.door.do_close()
    assert not ss.can_see(dd)
    ss.add_aggro(dd)
    mobs.start()
    mcp.run()
    me.do("pass")
    mcp.run()
    assert not ss.aggro
    assert not mobs.fighting
