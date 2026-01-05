# coding: utf-8


def test_visicalc_from_nw_room(vroom):
    vroom.v_map[2, 2] = vroom.o.me

    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (5, 7),
        (6, 3),
        (6, 4),
        (6, 5),
        (6, 6),
        (6, 7),
        (6, 8),
        (6, 9),
        (7, 3),
        (7, 4),
        (7, 5),
        (7, 6),
        (7, 7),
        (7, 8),
        (7, 9),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 6),
        (8, 7),
        (8, 8),
        (8, 9),
        (9, 3),
        (9, 4),
        (10, 4),
    }
    assert visible == correct


def test_visicalc_from_ne_room_door_closed(vroom):
    vroom.v_map[8, 1] = vroom.o.me
    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {(1, 1), (1, 2)}
    assert visible == correct


def test_visicalc_from_ne_room_door_open(vroom):
    vroom.v_map[8, 1] = vroom.o.me
    vroom.v_map.get(8, 2).do_open()

    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {
        (1, 6),
        (1, 7),
        (1, 8),
        (1, 9),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (2, 8),
        (2, 9),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (3, 8),
        (3, 9),
    }
    assert visible == correct


def test_visicalc_from_middle_area(vroom):
    vroom.v_map[8, 3] = vroom.o.me
    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {
        (1, 2),
        (1, 3),
        (2, 2),
        (2, 3),
        (3, 2),
        (3, 3),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (5, 2),
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (5, 7),
        (5, 8),
        (6, 2),
        (6, 3),
        (6, 4),
        (6, 5),
        (6, 6),
        (6, 7),
        (6, 8),
        (7, 2),
        (7, 3),
        (7, 4),
        (7, 5),
        (7, 6),
        (7, 7),
        (7, 8),
        (8, 1),
        (8, 2),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 6),
        (8, 7),
        (8, 8),
        (9, 2),
        (9, 3),
        (10, 2),
        (10, 3),
    }
    assert visible == correct


def test_visicalc_from_lower_room(vroom):
    vroom.v_map[4, 9] = vroom.o.me
    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (1, 5),
        (1, 6),
        (1, 7),
        (1, 8),
        (1, 9),
        (2, 3),
        (2, 4),
        (2, 5),
        (2, 6),
        (2, 7),
        (2, 8),
        (2, 9),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (3, 7),
        (3, 8),
        (3, 9),
        (4, 3),
        (4, 4),
        (4, 5),
        (4, 6),
        (4, 7),
        (4, 8),
        (4, 9),
        (5, 2),
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (5, 7),
        (5, 8),
        (5, 9),
        (6, 3),
        (6, 4),
        (7, 1),
        (7, 2),
        (7, 3),
    }
    assert visible == correct


def test_visicalc_from_skeleton_position(vroom):
    vroom.v_map[1, 2] = vroom.o.me
    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me) if c and c.visible}
    correct = {
        (1, 1),
        (1, 2),
        (1, 3),
        (1, 4),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 4),
        (4, 5),
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (6, 3),
        (6, 4),
        (6, 5),
        (6, 6),
        (6, 7),
        (7, 3),
        (7, 4),
        (7, 5),
        (7, 6),
        (7, 7),
        (7, 8),
        (8, 3),
        (8, 4),
        (8, 5),
        (8, 6),
        (8, 7),
        (8, 8),
        (9, 3),
        (9, 4),
        (10, 3),
        (10, 4),
    }
    assert visible == correct


def test_visicalc_maxdist(vroom):
    vroom.v_map.get(8, 2).do_open()
    vroom.v_map[8, 3] = vroom.o.me

    visible = {pos for pos, c in vroom.v_map.visicalc_submap(vroom.o.me, maxdist=3) if c and c.visible}
    correct = {
        (0, 3),
        (1, 3),
        (1, 4),
        (1, 5),
        (2, 3),
        (2, 4),
        (2, 5),
        (3, 1),
        (3, 2),
        (3, 3),
        (3, 4),
        (3, 5),
        (3, 6),
        (4, 3),
        (4, 4),
        (5, 3),
        (5, 4),
    }
    assert visible == correct
