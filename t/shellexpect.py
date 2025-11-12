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

CC = re.compile(r"\x1b\[([\d;]*)([ABCDEFGHJKLMPXacdefghlmnqrsu])")


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


class Cursor:
    def __init__(self, row=0, col=0, height=25, width=80):
        self.row = row
        self.col = col
        self.height = height
        self.width = width

    def wrap(self):
        scroll = False
        if self.col >= self.width:
            self.col = 0
            self.row += 1
        if self.row >= self.height:
            self.row = self.height - 1
            scroll = True
        return scroll

    def move(self, row=0, col=0):
        # ansi \x1b[1;1H should be (0,0) in our matrix
        # subtract one, but enforce a position that makes sense
        self.row = min(self.height - 1, max(0, row - 1))
        self.col = min(self.width - 1, max(0, col - 1))

    def __iter__(self):
        return (self.row, self.col)

    def __repr__(self):
        return f"Cursor<{self.row}, {self.col}>"


class Screen(list):
    def __init__(self, width=80, height=25):
        self.width = width
        self.height = height
        self.cursor = Cursor(height=height, width=width)
        self._row = " " * width
        super().__init__(self._row for _ in range(height))

    def append_char(self, x):
        if len(x) != 1:
            raise ValueError(f"invalid: {x}")
        if self.cursor.wrap():
            self.append(self._row)
            self.pop(0)
        line = self[self.cursor.row]
        self[self.cursor.row] = line[: self.cursor.col] + x + line[self.cursor.col + 1 :]
        self.cursor.col += 1

    def write(self, x):
        for c in x:
            self.append_char(c)

    def move(self, row=0, col=0):
        self.cursor.move(row=row, col=col)

    def __repr__(self):
        bar = f'+{"-" * len(self[0])}+'
        tmp = [f"|{x}|" for x in self]
        tmp = [bar, *tmp, bar, f" {self.cursor}"]
        return "\n".join(tmp)


def render_terminal(text, width=80, height=25):
    alt = Screen()
    cur = pri = Screen()

    while text:
        if m := CC.search(text):
            text = text[len(m.group(0)) :]
            data, code = m.groups()
            if code == "m":
                pass
            elif code == "H":
                v = [int(x) for x in data.split(";")]
                if len(v) == 2:
                    cursor.move(*v)
                else:
                    raise ValueError(f"invalid mnove code: {m.group(0)!r}")
        else:
            cur.append_char(text[0])
            text = text[1:]

    return cur
