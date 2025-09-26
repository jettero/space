# coding: utf-8

def test_look_shows_living_over_door(a_map, objs):
    objs.me.do("open door; s")

    # Render the visible map and ensure the living '@' appears
    sub = a_map.visicalc_submap(objs.me)
    txt = sub.text_drawing
    assert "@" in txt
