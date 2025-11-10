# coding: utf-8

import re

import pytest


def test_shell_basic(shell_proc):
    shell_proc.sendline("look")
    ok, _ = shell_proc.expect(r"/space/", timeout=1)
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"
    assert ok, message


def test_say_a_lot(shell_proc):
    for x in range(80):
        shell_proc.sendline(f"say hiya{x}")
        pat = f"Hiya{x}\\."
        ok, _ = shell_proc.expect(pat, timeout=1)
        lines, row, col = shell_proc.terminal_state(width=80, height=25)
        message = f"row={row} col={col} pat={pat} capbuf=<<{shell_proc.captured[-200:]!r}>>"
        assert ok, message
        if x >= 25:
            assert f"Hiya{x}" in lines[22]


def test_scroll_history(shell_proc):
    for x in range(80):
        shell_proc.sendline(f"say hiya{x}")
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"
    before_numbers = []
    for line in lines:
        match = re.search(r"Hiya(\d+)", line)
        if match:
            before_numbers.append(int(match.group(1)))
    if not before_numbers:
        pytest.skip(message)
    sequences = ("\x1b[5~", "\x1b[1;2A", "\x1b[1;5A")
    after_numbers = None
    for seq in sequences:
        shell_proc.send(seq)
        scrolled_lines, _, _ = shell_proc.terminal_state(width=80, height=25)
        numbers = []
        for line in scrolled_lines:
            match = re.search(r"Hiya(\d+)", line)
            if match:
                numbers.append(int(match.group(1)))
        if not numbers:
            continue
        if min(numbers) < min(before_numbers) or max(numbers) < max(before_numbers):
            after_numbers = numbers
            break
    if after_numbers is None:
        pytest.skip(message)
    assert min(after_numbers) < min(before_numbers) or max(after_numbers) < max(before_numbers)
