# coding: utf-8

import os
import pty
import signal
import subprocess
import termios
import fcntl
import select
import sys
from contextlib import contextmanager
import pytest


class ExpectProc:
    def __init__(self, argv, cwd=None, env=None):
        self.argv = argv
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.pid = None
        self.master = None
        self.slave = None

    def spawn(self):
        self.master, self.slave = pty.openpty()
        flags = fcntl.fcntl(self.master, fcntl.F_GETFL)
        fcntl.fcntl(self.master, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.pid = os.fork()
        if self.pid == 0:
            os.setsid()
            os.close(self.master)
            os.dup2(self.slave, 0)
            os.dup2(self.slave, 1)
            os.dup2(self.slave, 2)
            if self.slave > 2:
                os.close(self.slave)
            os.execvpe(self.argv[0], self.argv, self.env)
        os.close(self.slave)
        return self

    def send(self, s):
        os.write(self.master, s.encode())

    def sendline(self, s):
        os.write(self.master, (s + "\n").encode())

    def read(self, timeout=1.0, max_bytes=65536):
        out = bytearray()
        r, _, _ = select.select([self.master], [], [], timeout)
        if r:
            try:
                out.extend(os.read(self.master, max_bytes))
            except BlockingIOError:
                pass
        return out.decode(errors="ignore")

    def expect(self, needle, timeout=3.0):
        buf = []
        end = os.times()[4] + timeout
        while os.times()[4] < end:
            chunk = self.read(timeout=0.1)
            if chunk:
                buf.append(chunk)
                if needle in chunk or needle in "".join(buf):
                    return True, "".join(buf)
        return False, "".join(buf)

    def close(self, sig=signal.SIGTERM):
        if self.pid:
            try:
                os.kill(self.pid, sig)
            except ProcessLookupError:
                pass
        if self.master is not None:
            try:
                os.close(self.master)
            except OSError:
                pass


@contextmanager
def spawn(argv, cwd=None, env=None):
    proc = ExpectProc(argv, cwd=cwd, env=env).spawn()
    try:
        yield proc
    finally:
        proc.close()


@pytest.fixture
def shell_proc(tmp_path):
    # mirror lrun-shell.py behavior but as a subprocess target
    code = (
        "import sys;"
        "from t.troom import a_map, o;"
        "from space.master import MasterControlProgram as MCP;"
        "c=sys.argv[1:];"
        "c=['open door; sSW6s2w; get bauble'] if c[0:2] in ([""get"",""bauble""],[""bauble""],[""ubi"]) else ['look'];"
        "MCP().start_instance(type='local', username='jettero', map=a_map, body=o.me, init=c)"
    )
    script = tmp_path / "_shell_entry.py"
    script.write_text(code)
    with spawn([sys.executable, str(script)]) as p:
        yield p
