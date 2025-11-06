# coding: utf-8

from t.shellexpect import render_terminal


def test_render_basic():
    lines, row, col = render_terminal("abc")
    assert lines == ["abc"]
    assert row == 0
    assert col == 3


def test_render_carriage_return_overwrite():
    lines, row, col = render_terminal("abc\rA")
    assert lines == ["Abc"]
    assert row == 0
    assert col == 1


def test_render_colors_and_clear():
    lines, row, col = render_terminal("\x1b[32mhi\x1b[0m\nmore\r\x1b[K")
    assert lines[0] == "hi"
    assert lines[1] == ""
    assert row == 1
    assert col == 0


def test_prompt_bottom(shell_proc):
    shell_proc.expect(r"/space/ ", timeout=1)
    for _ in range(10):
        shell_proc.sendline("look")
    while True:
        ok, _ = shell_proc.expect(r"/space/ ", timeout=1)
        if not ok:
            break
    shell_proc.drain()
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    assert row == 24
    assert lines[-1] == "/space/ "
    assert row == len(lines)-1
    assert col == len(lines[-1])
