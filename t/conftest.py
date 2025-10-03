# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest


class TRoom:
    def __init__(self):
        import troom

        self.a_map, self.o = troom.gen_troom()


class ERoom:
    def __init__(self):
        import eroom

        self.e_map, self.o = eroom.gen_eroom()


@pytest.fixture
def troom():
    return TRoom()


@pytest.fixture
def objs(troom):
    return troom.o


@pytest.fixture
def a_map(troom):
    return troom.a_map


@pytest.fixture
def eroom():
    return ERoom()


@pytest.fixture
def e_map(eroom):
    return eroom.e_map
