# coding: utf-8

from space.living.msg import ReceivesMessages
from space.shell.list import Shell as ListShell


def test_simple_and_targeted_delivery(a_map, objs):
    objs.me.shell = ListShell()
    objs.dig_dug.shell = ListShell()

    objs.me.do("open door; sSW6s3w; look")
    assert len(objs.me.shell.msgs) == 6  # open door, move, look,map, look,map
    assert len(objs.dig_dug.shell.msgs) == 4 # open, move, look, look

    objs.me.simple_action("$N $vwave.")
    assert len(objs.me.shell.msgs) == 7
    assert len(objs.dig_dug.shell.msgs) == 5
    assert objs.me.shell.msgs[-1] == "You wave."
    assert objs.dig_dug.shell.msgs[-1] == "Paul waves."
