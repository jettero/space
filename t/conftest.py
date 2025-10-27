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


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        loc = rep.location[0]
        line = rep.location[1] + 1
        head = str(rep.longrepr) if hasattr(rep, "longrepr") else ""
        first = head.splitlines()[0] if head else ""
        log.error("FAIL %s:%d %s", loc, line, first)
        if hasattr(rep, "longrepr") and hasattr(rep.longrepr, "reprcrash"):
            r = rep.longrepr
            paths = []
            if hasattr(r, "reprtraceback") and hasattr(r.reprtraceback, "reprentries"):
                for e in r.reprtraceback.reprentries:
                    if hasattr(e, "reprfileloc") and hasattr(e.reprfileloc, "path"):
                        p = e.reprfileloc.path
                        lno = getattr(e.reprfileloc, "lineno", None)
                        if p and lno is not None:
                            paths.append(f"{p}:{lno}")
                        elif p:
                            paths.append(str(p))
            if paths:
                log.error("STACK %s", "; ".join(paths))
    if rep.when == "setup" and rep.failed:
        loc = rep.location[0]
        line = rep.location[1] + 1
        msg = str(rep.longrepr) if hasattr(rep, "longrepr") else ""
        log.error("ERROR during setup %s:%d %s", loc, line, msg.splitlines()[0] if msg else "")
    if rep.when == "teardown" and rep.failed:
        loc = rep.location[0]
        line = rep.location[1] + 1
        msg = str(rep.longrepr) if hasattr(rep, "longrepr") else ""
        log.error("ERROR during teardown %s:%d %s", loc, line, msg.splitlines()[0] if msg else "")
    return rep
