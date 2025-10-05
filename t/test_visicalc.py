# coding: utf-8


def test_visicalc_blocked_by_door(a_map):
    # In troom, between (8,1) and east partition there is a BlockedCell with a door.
    from t.troom import o as to

    me = to.me  # at (8,1)
    m = me.location.map

    # Choose a target to the south so the ray must pass through the door cell at (8,2)
    target = m.get(8, 3)
    assert target is not None

    # Before visicalc, mark should be reset by visicalc()
    m.visicalc(me, maxdist=10)
    # The cell beyond a closed door should not be visible
    assert target.visible is False

    # Open the door; LOS should now pass
    bc = m.get(8, 2)
    assert bc is not None and bc.has_door
    bc.do_open()
    m.visicalc(me, maxdist=10)
    assert target.visible is True
