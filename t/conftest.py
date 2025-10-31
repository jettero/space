# coding: utf-8
# pylint: disable=redefined-outer-name

import pytest
from space.shell.list import Shell as ListShell
import logging

log = logging.getLogger(__name__)


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


@pytest.fixture
def me_dd_ss(objs):
    objs.me.do("open door; sSWss")
    assert objs.me.location.pos == (7, 5), "Problem constructing fixture. open, move, or parser is busted"
    objs.me.shell = ListShell()
    objs.dig_dug.shell = ListShell()
    objs.stupid.shell = ListShell()
    return objs.me, objs.dig_dug, objs.stupid


@pytest.fixture
def me(me_dd_ss):
    return me_dd_ss[0]


@pytest.fixture
def dd(me_dd_ss):
    return me_dd_ss[1]


@pytest.fixture
def ss(me_dd_ss):
    return me_dd_ss[2]


def pytest_sessionfinish(session, exitstatus):
    log.info("pytest_sessionfinish(..., %d)", exitstatus)
    # The below is not in any way necessary. sometimes it feels like
    # last-pytest-run.log truncates on a pytest crash.  It doesn't, but the
    # below makes me fell better about it.
    for h in logging.getLogger().handlers:
        if getattr(h, "stream", None) and not getattr(h.stream, "closed", False):
            h.flush()
    for lg in logging.Logger.manager.loggerDict.values():
        if isinstance(lg, logging.Logger):
            for h in lg.handlers:
                if getattr(h, "stream", None) and not getattr(h.stream, "closed", False):
                    h.flush()


def pytest_assertrepr_compare(config, op, left, right):
    import pprint

    return ["", f"OP:  ¿{op}?", f"LHS: {pprint.pformat(left, width=4000)}", f"RHS: {pprint.pformat(right, width=4000)}"]
