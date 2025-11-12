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
        self.row = min(self.height - 1, max(0, row - 1))
        self.col = min(self.width - 1, max(0, col - 1))

    def clamp(self):
        if self.col < 0:
            self.col = 0
        elif self.col >= self.width:
            self.col = self.width - 1
        if self.row < 0:
            self.row = 0
        elif self.row >= self.height:
            self.row = self.height - 1

    def shift(self, rows=0, cols=0):
        self.row += rows
        self.col += cols
        self.clamp()

    def column(self, col=1):
        self.col = min(self.width - 1, max(0, col - 1))

    def home(self):
        self.row = 0
        self.col = 0

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

    def _scroll(self, count=1):
        for _ in range(count):
            list.append(self, self._row)
            list.pop(self, 0)
        self.cursor.row = self.height - 1

    def append_char(self, x):
        if len(x) != 1:
            raise ValueError(f"invalid: {x}")
        if self.cursor.wrap():
            self._scroll()
        line = self[self.cursor.row]
        self[self.cursor.row] = line[: self.cursor.col] + x + line[self.cursor.col + 1 :]
        self.cursor.col += 1

    def write(self, x):
        for c in x:
            self.append_char(c)

    def move(self, row=0, col=0):
        self.cursor.move(row=row, col=col)

    def newline(self, count=1):
        for _ in range(count or 1):
            self.cursor.col = 0
            self.cursor.row += 1
            if self.cursor.row >= self.height:
                self._scroll()

    def carriage_return(self):
        self.cursor.col = 0

    def backspace(self, count=1):
        self.cursor.col = max(self.cursor.col - (count or 1), 0)

    def clear_line_end(self):
        line = self[self.cursor.row]
        self[self.cursor.row] = line[: self.cursor.col] + " " * (self.width - self.cursor.col)

    def clear_line_start(self):
        line = self[self.cursor.row]
        self[self.cursor.row] = " " * (self.cursor.col + 1) + line[self.cursor.col + 1 :]

    def clear_line(self):
        self[self.cursor.row] = self._row

    def clear_screen(self, mode=0):
        if mode == 2:
            self[:] = [self._row for _ in range(self.height)]
            self.cursor.home()
            return
        if mode == 1:
            top = self.cursor.row
            for idx in range(top):
                self[idx] = self._row
            line = self[self.cursor.row]
            self[self.cursor.row] = " " * (self.cursor.col + 1) + line[self.cursor.col + 1 :]
            return
        self.clear_line_end()
        for idx in range(self.cursor.row + 1, self.height):
            self[idx] = self._row

    def __repr__(self):
        bar = f'+{"-" * len(self[0])}+'
        tmp = [f"|{x}|" for x in self]
        tmp = [bar, *tmp, bar, f" {self.cursor}"]
        return "\n".join(tmp)


def render_terminal(text, width=80, height=25):
    width = width or 80
    height = height or 25
    pri = Screen(width=width, height=height)
    alt = Screen(width=width, height=height)
    cur = pri
    cursor = cur.cursor
    saved = (0, 0)

    idx = 0
    size = len(text)
    while idx < size:
        ch = text[idx]
        if ch == "\x1b":
            if text.startswith("\x1b]", idx):
                if (end := text.find("\x07", idx)) == -1:
                    break
                idx = end + 1
                continue
            if text.startswith("\x1b7", idx):
                saved = (cursor.row, cursor.col)
                idx += 2
                continue
            if text.startswith("\x1b8", idx):
                cursor.row, cursor.col = saved
                cursor.clamp()
                idx += 2
                continue
            if (m := CC.match(text, idx)) is not None:
                idx = m.end()
                data, code = m.groups()
                params = [int(x) for x in data.split(";") if x != ""]
                if code == "m":
                    continue
                if code in ("H", "f"):
                    cursor.move(row=params[0] if params else 1, col=params[1] if len(params) > 1 else 1)
                    continue
                if code in ("A",):
                    cursor.shift(rows=-(params[0] if params else 1))
                    continue
                if code in ("B", "e"):
                    cursor.shift(rows=params[0] if params else 1)
                    continue
                if code in ("C", "a"):
                    cursor.shift(cols=params[0] if params else 1)
                    continue
                if code == "D":
                    cursor.shift(cols=-(params[0] if params else 1))
                    continue
                if code == "E":
                    cursor.shift(rows=params[0] if params else 1)
                    cursor.column(1)
                    continue
                if code == "F":
                    cursor.shift(rows=-(params[0] if params else 1))
                    cursor.column(1)
                    continue
                if code == "G":
                    cursor.column(params[0] if params else 1)
                    continue
                if code == "d":
                    cursor.row = min(cur.height - 1, max(0, (params[0] if params else 1) - 1))
                    continue
                if code == "J":
                    cur.clear_screen(params[0] if params else 0)
                    continue
                if code == "K":
                    mode = params[0] if params else 0
                    if mode == 0:
                        cur.clear_line_end()
                    elif mode == 1:
                        cur.clear_line_start()
                    else:
                        cur.clear_line()
                    continue
                if code == "L":
                    count = params[0] if params else 1
                    for _ in range(count):
                        cur.insert(cursor.row, cur._row)
                        cur.pop()
                    continue
                if code == "M":
                    count = params[0] if params else 1
                    if count > cur.height - cursor.row:
                        count = cur.height - cursor.row
                    for _ in range(count):
                        list.pop(cur, cursor.row)
                        list.append(cur, cur._row)
                    continue
                if code == "P":
                    count = params[0] if params else 1
                    if count > cur.width - cursor.col:
                        count = cur.width - cursor.col
                    if count <= 0:
                        continue
                    line = cur[cursor.row]
                    cur[cursor.row] = line[: cursor.col] + line[cursor.col + count :] + " " * count
                    continue
                if code == "X":
                    count = params[0] if params else 1
                    if count <= 0:
                        continue
                    line = cur[cursor.row]
                    cur[cursor.row] = (
                        line[: cursor.col] + " " * min(count, cur.width - cursor.col) + line[cursor.col + count :]
                    )
                    continue
                if code == "s":
                    saved = (cursor.row, cursor.col)
                    continue
                if code == "u":
                    cursor.row, cursor.col = saved
                    cursor.clamp()
                    continue
                continue
            if text.startswith("\x1b[", idx):
                idx += 2
                while idx < size and not ("@" <= (c := text[idx]) <= "~"):
                    idx += 1
                if idx < size:
                    idx += 1
                continue
            idx += 1
            continue
        if ch == "\n":
            cur.newline()
            idx += 1
            continue
        if ch == "\r":
            cur.carriage_return()
            idx += 1
            continue
        if ch == "\b":
            cur.backspace()
            idx += 1
            continue
        if ch == "\t":
            if (target := ((cursor.col // 8) + 1) * 8) >= cur.width:
                cursor.col = cur.width - 1
            else:
                cursor.col = target
            idx += 1
            continue
        if ch in ("\x0b", "\x0c"):
            cur.newline()
            idx += 1
            continue
        if ch == "\x07":
            idx += 1
            continue
        cur.append_char(ch)
        idx += 1

    lines = []
    for idx, raw in enumerate(cur):
        trimmed = raw.rstrip()
        if idx == cursor.row and cursor.col > len(trimmed):
            trimmed += " " * (cursor.col - len(trimmed))
        lines.append(trimmed)
    if not lines:
        lines.append("")
    row = cursor.row
    if row == height - 2 and lines and lines[-1] == "":
        lines = ["", *lines[:-1]]
        row += 1
    minimum = row + 1
    while len(lines) > minimum and lines[-1] == "":
        lines.pop()
    return lines, row, cursor.col
