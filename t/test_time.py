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
    assert not any("It's your turn" in m for m in me.shell.msgs)


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


def test_status(fight, me, dd, mcp):
    bar = "Round 1 │ ▸ Paul · Dig Dug · skellyman │ "
    assert me.shell.msgs[-1] == bar + "your turn: 2/2 main · 1/1 small"
    assert bar + "waiting on Paul" in dd.shell._queue
    me.do("2s")
    mcp.run()
    assert me.shell.msgs[-1] == bar + "your turn: 1/2 main · 1/1 small · 4 cells"
    dd.hurt(dd.hp - 1)
    me.do("2n; attack dig dug")
    mcp.run()
    assert me.shell.msgs[-2:] == ["The fight is over.", ""]


def test_attack_unconscious_is_free_hit(mobs, me, dd, mcp):
    dd.hurt(dd.hp)
    hp = dd.hp
    assert me.do("attack dig dug")
    assert dd.hp < hp
    assert not mobs.round


def test_target_reacts(mobs, me, dd, mcp, monkeypatch):
    seen = []
    monkeypatch.setattr(dd, "react_to_attack", lambda a, t: seen.append((a, t)))
    me.do("attack dig dug")
    assert seen == [(me, dd)]


def test_witness_without_los_no_reaction(objs, a_map, mobs, me, dd, ss, mcp, monkeypatch):
    a_map[8, 1] = ss
    objs.door.do_close()
    assert not ss.can_see(me) and not ss.can_see(dd)
    seen = []
    monkeypatch.setattr(ss, "react_to_attack", lambda a, t: seen.append((a, t)))
    me.do("attack dig dug")
    assert not seen


def test_witness_joins(mobs, me, dd, ss, mcp, monkeypatch):
    assert ss.can_see(me)
    monkeypatch.setattr(ss, "react_to_attack", lambda a, t: ss.add_aggro(a))
    me.do("attack dig dug")
    assert me in ss.aggro


def test_witness_objects_to_free_hit(mobs, me, dd, ss, mcp, monkeypatch):
    dd.hurt(dd.hp)
    hp = dd.hp
    monkeypatch.setattr(ss, "react_to_attack", lambda a, t: ss.add_aggro(a))
    assert me.do("attack dig dug")
    assert dd.hp < hp
    assert mobs.round == 1


def test_unconscious_cannot_act(dd):
    dd.hurt(dd.hp)
    for cmd in ("say hi", "smile"):
        assert not dd.do(cmd)
        assert dd.shell.msgs[-1] == "You can't do that while unconscious."
    assert dd.do("sheet")


def test_unconscious_inventory_is_private(dd, monkeypatch):
    seen = []
    dd.hurt(dd.hp)
    monkeypatch.setattr(dd, "simple_action", lambda *a, **kw: seen.append(a))
    assert dd.do("inventory")
    assert not seen


def test_unconscious_mob_no_growl(mobs, dd, monkeypatch):
    seen = []
    monkeypatch.setattr(dd, "simple_action", lambda *a, **kw: seen.append(a))
    dd.add_aggro(dd)
    dd.shell.round_start(1)
    assert seen
    dd.hurt(dd.hp)
    seen.clear()
    dd.shell.round_start(1)
    assert not seen


def test_unconscious_skip_initiative(mobs, me, ss, mcp):
    ss.hurt(ss.hp)
    me.do("attack dig dug")
    assert me in mobs.actors and ss not in mobs.actors


def test_unconscious_voicelines(dd, monkeypatch):
    seen = []
    monkeypatch.setattr(dd, "voiceline_frequency", True)
    monkeypatch.setattr(dd, "simple_action", lambda *a, **kw: seen.append(a))
    dd.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert seen
    dd.hurt(dd.hp)
    seen.clear()
    dd.do_receive(":EOF:YOUR_TURN:", your_turn=True)
    assert not seen


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
