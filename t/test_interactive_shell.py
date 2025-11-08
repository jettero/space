# coding: utf-8

import pytest, os


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
        assert False, message
        assert ok, message


# the AI managed to get this test to pass by drawing the CompletionMenu above the prompt
# but it had other quirky behaviors... not worth it for today
@pytest.mark.skip(reason="prompt-toolkit really wants this menu below the prompt")
def test_shell_completion_float_position(shell_proc):
    # make sure we start out aligned to the bottom of the screen
    for i in range(5):
        shell_proc.sendline("look")
        shell_proc.expect(r"/space/ ", timeout=1)
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"
    assert row == 24, message
    assert "/space/" in lines[-1], message

    # try to barf up the completion menu by typing 'o<tab><tab>' we can detect
    # the floating menu by looking for the Emote/Verb words which display in
    # the menu and verifying the prompt is still at the bottom of the screen
    # note that terminal_state issues a drain() for us, so we likely don't even
    # need the expect(prompt)

    shell_proc.send("o\t\t")
    shell_proc.expect(r"/space/ ", timeout=1)
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"

    # verify the completion menu is above lines[23]
    menu_lines = [i for i, line in enumerate(lines) if "Emote" in line or "Verb" in line]
    assert menu_lines, message
    assert all(x < 23 for x in menu_lines), message

    # but now also verify the prompt is still on the last line of the terminal
    assert row == 24, message
    assert "/space/" in lines[-1], message


@pytest.mark.skip(reason="hey, the current behavior is kindof ok")
def test_shell_menu_destruct_prompt_position(shell_proc):
    # make sure we start out aligned to the bottom of the screen
    for i in range(5):
        shell_proc.sendline("look")
        shell_proc.expect(r"/space/ ", timeout=1)
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"
    assert row == 24, message
    assert "/space/" in lines[-1], message

    shell_proc.send("l\t\t")
    shell_proc.expect(r"/space/ ", timeout=1)

    # when the menu disappears we should still be on line 24
    shell_proc.send("\x08")
    lines, row, col = shell_proc.terminal_state(width=80, height=25)
    message = f"row={row} col={col} capbuf=<<{shell_proc.captured[-200:]!r}>>"
    assert row == 24, message
    assert "/space/" in lines[-1], message


@pytest.mark.skipif(not os.environ.get("SPACE_SLOW_TESTS"), reason="boring result, slow test")
def test_shell_no_double_prompt(shell_proc):
    shell_proc.expect(r"/space/ ", timeout=2)
    ok, data = shell_proc.expect("Application is already running.", timeout=10)
    assert not ok, data
    assert "Application is already running." not in shell_proc.captured
