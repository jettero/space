# coding: utf-8

import types

from space.find import lazy_find_verb_method


class Dummy:
    do_say_words = lazy_find_verb_method("say", "do_say_words")


def test_lazy_descriptor_installs_on_first_access():
    d = Dummy()
    # First attribute access should materialize and replace the descriptor
    bound = d.do_say_words  # noqa: F841
    assert isinstance(Dummy.__dict__["do_say_words"], types.FunctionType)


def test_lazy_descriptor_subsequent_calls_use_installed_function():
    d = Dummy()
    # Access once to install
    _ = d.do_say_words
    fn1 = Dummy.__dict__["do_say_words"]
    # Access again; should be same function object on the class
    _ = d.do_say_words
    fn2 = Dummy.__dict__["do_say_words"]
    assert fn1 is fn2
