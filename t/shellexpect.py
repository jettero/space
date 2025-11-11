# coding: utf-8

import logging
import os
import re
import signal
import sys
import time
from collections import namedtuple
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
        self.captured = ""

    def spawn(self):
        self.child = pexpect.spawn(
            self.argv[0], self.argv[1:], cwd=self.cwd, env=self.env, encoding="utf-8", timeout=self.timeout
        )
        return self

    def send(self, s):
        self.child.send(s)

    def sendline(self, s):
        self.child.sendline(s)

    def drain(self, timeout=0.05):
        if self.child is None:
            return ""
        chunks = []
        timeout = timeout or self.timeout
        while True:
            try:
                self.child.expect(r".+", timeout=timeout)
            except (pexpect.TIMEOUT, pexpect.EOF, OSError):
                chunk = self.child.before
                if chunk:
                    chunks.append(chunk)
                break
            else:
                chunk = self.child.before + self.child.after
                if chunk:
                    chunks.append(chunk)
        if not chunks:
            return ""
        data = "".join(chunks)
        self.captured += data
        return data

    def read(self, timeout=1.0, max_bytes=65536):
        self.child.timeout = timeout or self.timeout
        try:
            self.child.expect(r".+", timeout=timeout)
        except Exception:
            return ""
        data = self.child.before + self.child.after
        self.captured += data
        return data

    def expect(self, needle, timeout=1.0):
        duration = self.timeout if timeout is None else timeout
        deadline = time.monotonic() + (duration or self.timeout)
        data = ""
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            step = remaining if remaining < 0.05 else 0.05
            try:
                self.child.expect(needle, timeout=step)
            except Exception:
                chunk = self.child.before
                if chunk:
                    data += chunk
                    self.captured += chunk
                    if isinstance(needle, str) and re.search(needle, "\n".join(render_terminal(self.captured, 0, 0)[0])):
                        return True, data
            else:
                chunk = self.child.before + self.child.after
                self.captured += chunk
                return True, chunk
        return False, data

    def close(self, sig=signal.SIGTERM):
        if self.child is not None:
            try:
                self.child.sendeof()
                self.child.expect(pexpect.EOF, timeout=self.timeout)
                self.child.terminate(force=True)
            except Exception:
                pass

    def terminal_state(self, width=80, height=25):
        self.drain()
        return render_terminal(self.captured, width, height)

    def terminal_picture(self, width=80, height=25):
        self.drain()
        lines, _, _ = render_terminal(self.captured, width, height)
        return "\n".join(lines)


@contextmanager
def ShellExpect(module, cwd=None, env=None):
    argv = [sys.executable, "-u", "-m", module]
    proc = ExpectProc(argv, cwd=cwd or os.path.dirname(os.path.dirname(__file__)), env=env).spawn()
    try:
        yield proc
    finally:
        proc.close()

def render_terminal(text, width=80, height=25):
    alt_lines = [" " * width for _ in range(height)]
    main_lines = [" " * width for _ in range(height)]
    cursor = namedtuple("Cursor", ['row', 'col'])(0,0)
    return lines, *cursor
