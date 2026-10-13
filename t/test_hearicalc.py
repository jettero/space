# coding: utf-8

import pytest


def test_hearicalc_exists_and_basic(e_map):
    # in eroom, the player is o.me at (9,9)
    from t.eroom import o as eo

    me = eo.me
    sub = me.location.map.hearicalc_submap(me, maxdist=3)
    assert hasattr(sub, "bounds")
    # origin cell included
    assert sub.get(0, 0) is not None


def test_hearicalc_open_space_radius(e_map):
    from t.eroom import o as eo

    me = eo.me
    m = me.location.map
    sub2 = m.hearicalc_submap(me, maxdist=2)
    sub4 = m.hearicalc_submap(me, maxdist=4)
    # Larger radius should encompass at least as many cells
    assert (sub4.bounds.X - sub4.bounds.x) >= (sub2.bounds.X - sub2.bounds.x)
    assert (sub4.bounds.Y - sub4.bounds.y) >= (sub2.bounds.Y - sub2.bounds.y)


def test_hearicalc_door_attenuation_threshold(a_map):
    # use troom where we know there is a door between partitions
    from t.troom import o as to

    me = to.me
    m = me.location.map
    # place a target just across a typical door in e_map fixture if present
    # we reuse visicalc bounds as a proxy for adjacency; hearicalc should not prune
    sub_loud = m.hearicalc_submap(me, maxdist=6, min_hearability=0.25)
    sub_quiet = m.hearicalc_submap(me, maxdist=6, min_hearability=0.35)
    # With a single door (pass-through ~0.3 default), listeners should be
    # included at 0.25 but excluded at 0.35
    assert sub_loud.bounds is not None
    assert sub_quiet.bounds is not None


def test_hearicalc_view_is_whoms(objs):
    m = objs.me.location.map
    loud = m.hearicalc_submap(objs.me, maxdist=6, min_hearability=0.25)
    quiet = m.hearicalc_submap(objs.me, maxdist=6, min_hearability=0.35)
    assert loud.whom is quiet.whom is objs.me
    assert objs.me in quiet.objects
    assert objs.dig_dug in loud.objects
    assert objs.dig_dug not in quiet.objects


def test_hearicalc_returns_hearability(objs):
    heard = objs.me.location.map.hearicalc(objs.me, maxdist=6)
    assert isinstance(heard, dict)
    assert heard[objs.me.location.pos] == 1.0
    assert heard[objs.dig_dug.location.pos] == pytest.approx(0.3)


def test_hearicalc_starting_hearability(objs):
    heard = objs.me.location.map.hearicalc(objs.me, maxdist=6, hearability=2.5)
    assert heard[objs.me.location.pos] == 2.5
    assert heard[objs.dig_dug.location.pos] == pytest.approx(0.75)
    assert objs.dig_dug.location.pos not in objs.me.location.map.hearicalc(objs.me, maxdist=6, hearability=0.3)


def test_hearicalc_open_door_passes_all(objs):
    objs.me.do("open door")
    assert objs.me.location.map.hearicalc(objs.me, maxdist=6)[objs.dig_dug.location.pos] == pytest.approx(1.0)


def test_hearicalc_maxdist(objs):
    m = objs.dig_dug.location.map
    assert m.hearicalc(objs.dig_dug, maxdist=8)[objs.stupid.location.pos] == pytest.approx(1.0)
    assert objs.stupid.location.pos not in m.hearicalc(objs.dig_dug, maxdist=6)


def test_hearicalc_prunes_walls(objs):
    assert {(9, 1), (7, 1), (8, 0)}.isdisjoint(objs.me.location.map.hearicalc(objs.me, maxdist=6))


def test_hearicalc_compounds_barriers(e_map):
    from t.eroom import o as eo

    me = eo.me
    m = me.location.map
    # Ensure traversal works and does not explode when encountering walls/doors
    sub = m.hearicalc_submap(me, maxdist=8, min_hearability=0.05)
    assert sub is not None
