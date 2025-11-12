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


def grab(shell_proc):
    lines, _, _ = shell_proc.terminal_state(height=25)
    picture = "\n".join(lines)
    with open("/tmp/picture.txt", "w") as fh:
        fh.write(picture)
    with open("/tmp/captured.txt", "w") as fh:
        fh.write(shell_proc.captured)
    base = [int(x) for x in re.findall(r"Hiya(\d+)", picture)]
    return base, f"base={base} first2={lines[:2]!r} last2={lines[-2:]!r}"


def test_scroll_history(shell_proc):
    for x in range(200):
        shell_proc.sendline(f"say hiya{x}")

    ok, _ = shell_proc.expect(r"Hiya199", timeout=1)
    base, msg = grab(shell_proc)

    assert ok, msg
    assert len(base) == 23, msg
    assert base[-1] == 199, msg
    assert base[0] == 177, msg

    # s-up: [1;2A
    shell_proc.sendline("\x1b[1;2A")
    base, msg = grab(shell_proc)
    assert len(base) == 23, msg
    assert base[-1] == 199, msg
    assert base[0] == 177, msg

    # s-dn: [1;2B
