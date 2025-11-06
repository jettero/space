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

    def drain(self, max_bytes=65536):
        if self.child is None:
            return ""
        chunks = []
        while True:
            try:
                chunk = self.child.read_nonblocking(max_bytes, 0)
            except (pexpect.TIMEOUT, pexpect.EOF, OSError):
                break
            if not chunk:
                break
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
        timeout = timeout or self.timeout
        try:
            self.child.expect(needle, timeout=timeout)
            data = self.child.before + self.child.after
            self.captured += data
            return True, data
        except Exception:
            data = self.child.before
            self.captured += data
            return False, data

    def close(self, sig=signal.SIGTERM):
        if self.child is not None:
            try:
                self.child.sendeof()
                self.child.expect(pexpect.EOF, timeout=self.timeout)
                self.child.terminate(force=True)
            except Exception:
                pass

    def capture(self):
        return self.captured

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
    proc = ExpectProc(argv, cwd=cwd, env=env).spawn()
    try:
        yield proc
    finally:
        proc.close()


def render_terminal(text, width=80, height=25):
    lines = [""]
    row = 0
    col = 0
    i = 0
    length = len(text)
    while i < length:
        ch = text[i]
        if ch == "\x1b":
            i, row, col = _consume_escape(text, i, row, col, lines, width, height)
            continue
        if ch == "\r":
            col = 0
        elif ch == "\n":
            row += 1
            row = _ensure_row(lines, row, height)
            col = 0
        elif ch == "\b":
            if col > 0:
                col -= 1
        elif ch == "\x07":
            pass
        else:
            row = _ensure_row(lines, row, height)
            current = lines[row]
            if col < len(current):
                lines[row] = current[:col] + ch + current[col + 1 :]
            else:
                if col > len(current):
                    lines[row] = current + " " * (col - len(current))
                lines[row] += ch
            col += 1
            if width and col >= width:
                row += 1
                row = _ensure_row(lines, row, height)
                col = 0
        i += 1
    return lines, row, col


def _consume_escape(text, index, row, col, lines, width, height):
    next_index = index + 1
    if next_index >= len(text):
        return len(text), row, col
    marker = text[next_index]
    if marker == "[":
        return _consume_csi(text, index, row, col, lines, width, height)
    if marker == "]":
        end = next_index + 1
        while end < len(text) and text[end] != "\x07":
            end += 1
        if end < len(text):
            end += 1
        return end, row, col
    if marker == "(":
        end = next_index + 1
        if end < len(text):
            end += 1
        return end, row, col
    return next_index + 1, row, col


def _consume_csi(text, index, row, col, lines, width, height):
    start = index + 2
    end = start
    while end < len(text) and text[end] < "@":
        end += 1
    if end >= len(text):
        return len(text), row, col
    final = text[end]
    params = text[start:end]
    parts = params.split(";") if params else []
    if final == "K":
        if row < len(lines):
            lines[row] = lines[row][:col]
    elif final == "G":
        target = _parse_param(parts, 0, 1) - 1
        if target < 0:
            target = 0
        col = target
    elif final == "A":
        delta = _parse_param(parts, 0, 1)
        row -= delta
        if row < 0:
            row = 0
    elif final == "B":
        row += _parse_param(parts, 0, 1)
        row = _ensure_row(lines, row, height)
    elif final == "C":
        col += _parse_param(parts, 0, 1)
    elif final == "D":
        delta = _parse_param(parts, 0, 1)
        col -= delta
        if col < 0:
            col = 0
    elif final in ("H", "f"):
        target_row = _parse_param(parts, 0, 1) - 1
        target_col = _parse_param(parts, 1, 1) - 1
        if target_row < 0:
            target_row = 0
        if target_col < 0:
            target_col = 0
        row = target_row
        col = target_col
        row = _ensure_row(lines, row, height)
    elif final == "J":
        if parts and parts[0] == "2":
            lines[:] = [""]
            row = 0
            col = 0
    if width and col >= width:
        extra = col // width
        col = col % width
        row += extra
        row = _ensure_row(lines, row, height)
    return end + 1, row, col


def _ensure_row(lines, row, height):
    while row >= len(lines):
        lines.append("")
    if height and len(lines) > height:
        overflow = len(lines) - height
        lines[:] = lines[overflow:]
        row -= overflow
        if row < 0:
            row = 0
    return row


def _parse_param(parts, index, default):
    if index >= len(parts):
        return default
    value = parts[index]
    return int(value) if value.isdigit() else default
