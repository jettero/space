# coding: utf-8
# pylint: disable=invalid-name,unused-argument

import pytest
from collections import namedtuple


class SayParam(namedtuple("SayParam", ["variant", "us", "them"])):
    def __repr__(self):
        return f"SayParam[{self.variant}]"

    __str__ = __repr__


def test_say_basic(me, dd):
    me.do("say hi")
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == 'You say, "Hi."'
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == 'Paul says, "Hi."'

    me.do("say hi!")
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == 'You exclaim, "Hi!"'
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == 'Paul exclaims, "Hi!"'

    me.do("say hi?")
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == 'You ask, "Hi?"'
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == 'Paul asks, "Hi?"'

    me.do("say er, gozer, are you a god?")
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == 'You ask, "Er, gozer, are you a god?"'
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == 'Paul asks, "Er, gozer, are you a god?"'


@pytest.mark.xfail(strict=False, reason="visicalc issues, will revisit")
@pytest.mark.parametrize(
    "sp",
    [
        SayParam("say hi :)", 'You happily declare, "Hi."', 'Paul happily declares, "Hi."'),
        SayParam("say hi :(", 'You sadly mumble, "Hi."', 'Paul sadly mumbles, "Hi."'),
        # XXX[busted]: SayParam("say hi ; )", 'You wink and suggest, "Hi."', 'Paul winks and suggests, "Hi."'),
        SayParam("say hi :0", 'You look shocked and say, "Hi."', 'Paul looks shocked and says, "Hi."'),
        SayParam("say hi :|", 'You sullenly state, "Hi."', 'Paul sullenly states, "Hi."'),
        SayParam("say hi :/", 'You smirk and say, "Hi."', 'Paul smirks and says, "Hi."'),
        SayParam("say hi :P", 'You stick out your tongue and say, "Hi."', 'Paul sticks out her tongue and says, "Hi."'),
        SayParam("say hi :p", 'You stick out your tongue and say, "Hi."', 'Paul sticks out her tongue and says, "Hi."'),
        SayParam("say hi =)", 'You smile brightly and say, "Hi."', 'Paul smiles brightly and says, "Hi."'),
        SayParam("say hi =<", 'You sarcastically state, "Hi."', 'Paul sarcastically states, "Hi."'),
        SayParam("say hi =>", 'You facetiously say, "Hi."', 'Paul facetiously says, "Hi."'),
        # XXX[busted]: SayParam("say \\o/", 'You throw your hands in the air and shout, ""', 'Paul throws his hands in the air and shouts, ""'),
        SayParam(
            "say (parenthetical)",
            'You interject parenthetically, "Parenthetical"',
            'Paul interjects parenthetically, "Parenthetical"',
        ),
    ],
)
def test_say_variants(me, dd, sp):
    me.do(sp.variant)
    assert len(me.shell.msgs) > 0 and me.shell.msgs[-1] == sp.us
    assert len(dd.shell.msgs) > 0 and dd.shell.msgs[-1] == sp.them


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
