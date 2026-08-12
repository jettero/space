# coding: utf-8

import pytest

from space.msg import BoxMessage, MapMessage, TextMessage
from space.shell.prompt import SpaceMessageLog


@pytest.fixture
def mlog():
    return SpaceMessageLog(limit=800, color=False, linger=8)


def map_rows(mlog):
    return [r for r in mlog.records if r.ephemeral]


def prose(mlog):
    return ["".join(f[1] for f in r.fragments) for r in mlog.records if not r.ephemeral]


def test_map_drawing_is_rigid_and_ephemeral_but_the_listing_is_not(me, a_map):
    lines = MapMessage(a_map.visicalc_submap(me), tb=me).render_lines(color=False)
    assert [x[1:] for x in lines if x[2]] == [(True, True)] * len([x for x in lines if x[2]])
    assert [x for x in lines if not x[2]], "the distance/object listing should not be ephemeral"
    assert not any(x[1] for x in lines if not x[2]), "the listing is prose, not rigid"


def test_a_new_map_supersedes_the_old_one(mlog, me, a_map):
    msg = MapMessage(a_map.visicalc_submap(me), tb=me)
    mlog.append(msg)
    first = len(map_rows(mlog))
    assert first > 1
    mlog.append(msg)
    assert len(map_rows(mlog)) == first, "the second map should have dropped the first"


def test_map_expires_after_linger_lines_of_text(mlog, me, a_map):
    mlog.append(MapMessage(a_map.visicalc_submap(me), tb=me))
    listing = prose(mlog)
    for i in range(mlog.linger - 1):
        mlog.append(TextMessage(f"tick {i}"))
    assert map_rows(mlog), "the map should still be here"
    mlog.append(TextMessage("one more"))
    assert not map_rows(mlog), "the map should have expired"
    assert prose(mlog)[: len(listing)] == listing, "the object listing survives the map"


def test_box_messages_are_rigid_and_permanent(mlog):
    mlog.append(BoxMessage("stats", ["a", "b"]))
    assert all(r.rigid for r in mlog.records)
    assert not map_rows(mlog)


def test_over_limit_records_are_trimmed_from_the_front():
    mlog = SpaceMessageLog(limit=10, color=False)
    for i in range(40):
        mlog.append(TextMessage(f"line {i}"))
    assert len(mlog) == 10
    assert prose(mlog) == [f"line {i}" for i in range(30, 40)]


def test_under_limit_records_are_kept():
    mlog = SpaceMessageLog(limit=10, color=False)
    for i in range(3):
        mlog.append(TextMessage(f"line {i}"))
    assert prose(mlog) == ["line 0", "line 1", "line 2"]
