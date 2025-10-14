# coding: utf-8
# pylint: disable=invalid-name,unused-argument

import pytest
from space.shell.list import Shell as ListShell


@pytest.fixture
def me(objs):
    objs.me.do("open door; sSWss")
    objs.me.shell = ListShell()
    return objs.me


@pytest.fixture
def dd(objs):
    objs.dig_dug.shell = ListShell()
    return objs.dig_dug


@pytest.fixture
def ss(objs):
    objs.stupid.shell = ListShell()
    return objs.stupid


def test_say_basic(me, dd):
    me.do("say hi")
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == 'You say, "Hi."'
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == 'Paul says, "Hi."'


# def test_shout_basic(a_map, objs):
#     objs.me.shell = ListShell()
#     objs.dig_dug.shell = ListShell()
#     objs.me.do('shout halp')
#     assert objs.me.shell.msgs[-1] == 'You shout, "Halp!"'
#     assert objs.dig_dug.shell.msgs[-1] == 'Paul shouts, "Halp!"'


# def test_emote_basic(a_map, objs):
#     objs.me.shell = ListShell()
#     objs.dig_dug.shell = ListShell()
#     objs.me.do('emote waves happily.')
#     assert objs.me.shell.msgs[-1] == 'Paul waves happily.'
#     assert objs.dig_dug.shell.msgs[-1] == 'Paul waves happily.'


# def test_tell_basic(a_map, objs):
#     objs.me.shell = ListShell()
#     objs.dig_dug.shell = ListShell()
#     objs.stupid.shell = ListShell()
#     objs.me.do(f'tell {objs.dig_dug.short} hi')
#     assert len(objs.me.shell.msgs)>0 and objs.me.shell.msgs[-1] == 'You tell Dig Dug, "hi."'
#     assert len(objs.dig_dug.shell.msg)>0 and objs.dig_dug.shell.msgs[-1] == 'Paul tells you, "hi."'
#     assert not objs.stupid.shell.msgs
