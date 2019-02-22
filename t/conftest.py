# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest

class TRoom:
    def __init__(self):
        import troom
        self.a_map, self.o = troom.gen_troom()

@pytest.fixture
def troom():
    return TRoom()

@pytest.fixture
def objs(troom):
    return troom.o

@pytest.fixture
def a_map(troom):
    return troom.a_map
