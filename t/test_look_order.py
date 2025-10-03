# coding: utf-8


def test_look_shows_living_over_door(a_map, objs):
    # space/parser.py +260 marks us active when we do something
    objs.me.do("open door; s; look")
    # space/parser.py +263 marks us in-active when we're done
    objs.me.active = True  # so we fake it like this

    # Render the visible map and ensure the living '@' appears
    sub = a_map.visicalc_submap(objs.me)
    txt = sub.text_drawing
    assert "@" in txt
