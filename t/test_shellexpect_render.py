# coding: utf-8

from t.shellexpect import render_terminal


def test_four_corners():
    captured = "\n".join(f"--- line {x}" for x in range(1, 26))
    captured += "\x1b[25;1H4\x1b[25;80H3\x1b[1;80H2\x1b[1;1H1"
    lines, row, col = render_terminal(captured)
    msg = f"row={row} col={col} lines={[lines[:2],lines[23:]]!r}"

    assert len(lines) == 25, msg
    assert len(lines[0]) == 80, msg
    assert len(lines[-1]) == 80, msg

    assert (row, col) == (0, 1), msg
    assert lines[0].startswith("1"), msg
    assert lines[0].endswith("2"), msg
    assert lines[24].startswith("4"), msg
    assert lines[24].endswith("3"), msg

    captured += "\x0a" * 25
    lines, row, col = render_terminal(captured)
    msg = f"row={row} col={col} lines={[lines[:2],lines[23:]]!r}"

    assert (row, col) == (24, 0), msg
    assert lines[0].startswith("--- line 2"), msg
    assert lines[1].startswith("--- line 3"), msg
    assert lines[23].startswith("4"), msg
    assert lines[23].endswith("3"), msg
    assert lines[24] == "", msg


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


def test_render_backspace_overwrite():
    lines, row, col = render_terminal("ab\bC")
    assert lines == ["aC"]
    assert row == 0
    assert col == 2


def test_render_cursor_navigation():
    lines, row, col = render_terminal("line1\nline2\x1b[A\x1b[3GX\x1b[B\x1b[2DY")
    assert lines == ["liXe1", "lYne2"]
    assert row == 1
    assert col == 2


def test_render_clear_screen():
    lines, row, col = render_terminal("old\nstuff\x1b[2Jnew")
    assert lines == ["new"]
    assert row == 0
    assert col == 3


def test_render_height_scroll():
    lines, row, col = render_terminal("one\ntwo\nthree\nfour", height=2)
    assert lines == ["three", "four"]
    assert row == 1
    assert col == 4


def test_render_osc_ignored():
    lines, row, col = render_terminal("\x1b]0;title\x07abc")
    assert lines == ["abc"]
    assert row == 0
    assert col == 3


def test_render_width_wraps():
    lines, row, col = render_terminal("abcd", width=3)
    assert lines == ["abc", "d"]
    assert row == 1
    assert col == 1


def test_render_prompt_toolkit_reprompt():
    lines, row, col = render_terminal("/space/ \r\x1b[2K\x1b[1G/space/ \x1b[9GOK")
    assert lines == ["/space/ OK"]
    assert row == 0
    assert col == 10


def test_render_prompt_toolkit_output_then_prompt():
    lines, row, col = render_terminal("/space/ cmd\r\nresult\r\n\x1b[2K\r\x1b[1G/space/ ")
    assert lines == ["/space/ cmd", "result", "/space/ "]
    assert row == 2
    assert col == 8
