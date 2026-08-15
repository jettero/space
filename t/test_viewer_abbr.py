# coding: utf-8

from space.find import set_this_body, this_body
from space.map.base import MapView
from space.map.util import Bounds


def nobody_active(*livings):
    set_this_body(None)
    for x in livings:
        x.active = False


def char_at(view, obj, viewer=None):
    drawing = view.text_drawing(viewer).split("\n")
    return drawing[obj.location.pos[1] - view.bounds.y][obj.location.pos[0] - view.bounds.x]


def test_viewer_is_at_with_nobody_active(a_map, me, dd):
    nobody_active(me, dd)
    view = a_map.visicalc_submap(me)
    assert (char_at(view, me, me), char_at(view, dd, me)) == ("@", "p")


def test_one_map_drawn_for_two_viewers(a_map, me, dd):
    nobody_active(me, dd)
    assert (char_at(a_map, me, me), char_at(a_map, dd, me)) == ("@", "p")
    assert (char_at(a_map, dd, dd), char_at(a_map, me, dd)) == ("@", "p")


def test_crop_drawn_for_a_viewer(me, dd):
    nobody_active(me, dd)
    assert char_at(MapView(me.vmap, Bounds.centered(me.location.pos, 5, 5)), me, me) == "@"


def test_map_without_a_viewer_draws_nobody_as_at(a_map, me, dd):
    nobody_active(me, dd)
    assert (char_at(a_map, me), char_at(a_map, dd)) == ("p", "p")


def test_drawing_does_not_disturb_turn_state(a_map, me, dd):
    nobody_active(me, dd)
    assert "@" in a_map.visicalc_submap(me).text_drawing(me)
    assert "@" in a_map.visicalc_submap(dd).text_drawing(dd, color=True)
    assert this_body() is None
    assert (me.active, dd.active) == (False, False)
