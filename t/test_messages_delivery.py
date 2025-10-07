# coding: utf-8

from space.living.msg import ReceivesMessages
from space.shell.list import Shell as ListShell


def test_simple_and_targeted_delivery(a_map, objs):
    objs.me.shell = ListShell()
    objs.dig_dug.shell = ListShell()

    objs.door.open = True
    objs.me.do_look()
    assert any(objs.door.abbr in x for x in objs.me.shell.msgs)

    objs.me.simple_action("$N $vwave.")
    assert len(objs.me.shell.msgs) == 3
    assert len(objs.dig_dug.shell.msgs) == 1
    assert objs.me.shell.msgs[-1] == "You wave."
    assert objs.dig_dug.shell.msgs[-1] == "Paul waves."
