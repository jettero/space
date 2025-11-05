# coding: utf-8

import os
import sys
import signal
import logging
from contextlib import contextmanager
import pytest
import pexpect


log = logging.getLogger(__name__)


class ExpectProc:
    def __init__(self, argv, cwd=None, env=None, timeout=1):
        self.argv = argv
        self.cwd = cwd
        self.env = env or os.environ.copy()
        self.timeout = timeout
        self.child = None

    def spawn(self):
        self.child = pexpect.spawn(
            self.argv[0], self.argv[1:], cwd=self.cwd, env=self.env, encoding="utf-8", timeout=self.timeout
        )
        return self

    def send(self, s):
        self.child.send(s)

    def sendline(self, s):
        self.child.sendline(s)

    def read(self, timeout=1.0, max_bytes=65536):
        self.child.timeout = timeout or self.timeout
        try:
            self.child.expect(r".+", timeout=timeout)
        except Exception:
            return ""
        return self.child.before + self.child.after

    def expect(self, needle, timeout=1.0):
        timeout = timeout or self.timeout
        try:
            self.child.expect(needle, timeout=timeout)
            return True, self.child.before + self.child.after
        except Exception:
            return False, self.child.before

    def close(self, sig=signal.SIGTERM):
        if self.child is not None:
            try:
                self.child.sendeof()
                self.child.expect(pexpect.EOF, timeout=self.timeout)
                self.child.terminate(force=True)
            except Exception:
                pass


@contextmanager
def ShellExpect(module, cwd=None, env=None):
    argv = [sys.executable, "-u", "-m", module]
    proc = ExpectProc(argv, cwd=cwd, env=env).spawn()
    try:
        yield proc
    finally:
        proc.close()
