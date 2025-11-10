# coding: utf-8


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
