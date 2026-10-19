import re

import pytest

from space.msg import TextMessage
from space.shell.prompt import Shell

from t.shellexpect import ShellEnv, build_screen, find_completion_extension, render_terminal


def hiya_numbers(lines):
    return [
        int(line[start + 4 : end]) for line in lines if (start := line.find("Hiya")) != -1 and (end := line.rfind('."')) != -1
    ]


@pytest.mark.parametrize("width,height", [(80, 25), (80, 35), (100, 35)])
def test_message_window_scrolls_half_page(width, height):
    with ShellEnv(width, height) as env:
        shell = env.shell
        for i in range(200):
            shell.receive_message(TextMessage(f'You say, "Hiya{i}."'))
        initial = env.render()
        info = shell.message_window.render_info
        expected = max(5, info.window_height // 2)
        env.trigger("shift-up")
        scrolled = env.render()
    initial_lines, _, _ = render_terminal(initial, width=width, height=height)
    scrolled_lines, _, _ = render_terminal(initial + scrolled, width=width, height=height)
    initial_numbers = hiya_numbers(initial_lines)
    scrolled_numbers = hiya_numbers(scrolled_lines)
    assert initial_numbers and scrolled_numbers
    assert len(initial_numbers) == len(scrolled_numbers)
    assert initial_numbers[0] - scrolled_numbers[0] == expected
    assert initial_numbers[-1] - scrolled_numbers[-1] == expected


@pytest.mark.parametrize("width,height", [(80, 25), (100, 25)])
def test_completions_menu_renders(width, height):
    lines, row, col = build_screen(
        [],
        "lo",
        width=width,
        height=height,
        setup=lambda env: env.set_completions("lo", index=0),
    )
    assert any("lol - Emote(lol)" in line for line in lines)
    assert any("look - Action(look)" in line for line in lines)
    assert row == height - 1
    assert col == len("/space/ lo")
    assert lines[-1] == "/space/ lo"


def above_rule(env):
    lines, _, _ = env.screen()
    return lines[next(i for i, l in enumerate(lines) if l.startswith("─")) - 1]


def test_fight_status_bar(me, dd, ss, mcp, monkeypatch):
    for b, r in ((me, 20), (dd, 10), (ss, 1)):
        monkeypatch.setattr(b.initiative, "roll", lambda r=r: r)
    with ShellEnv() as env:
        env.shell.owner = me
        assert "Round" not in above_rule(env)
        me.do("n")
        me.do("attack dig dug")
        mcp.run()
        assert above_rule(env).startswith("Round 1 │ ▸ Paul") and "your turn: 2/2 main" in above_rule(env)
        assert not any("It's your turn" in l for l in env.screen()[0])
        assert re.search(r"\x1b\[(?:[0-9;]*;)?7m[^\x1b]*Round 1", env.frames)


def test_render_lines_keeps_unchanged_rows():
    with ShellEnv() as env:
        first, _, _ = env.render_lines()
        env.shell.receive_message(TextMessage("Hiya."))
        second, _, _ = env.render_lines()
    assert any("Hiya." in l for l in second)
    assert second[-2:] == first[-2:]


def test_init_commands_run(me):
    with ShellEnv():
        assert Shell(owner=me, init=["look"]).message_log.records


def test_tab_completion_inserts_common_prefix():
    with ShellEnv() as env:
        doc, completions, extra = find_completion_extension(env)
        buf = env.apply_completions(doc, completions)
        env.trigger("tab")
        assert buf.text == doc.text + extra
        lines, _, _ = env.render_lines()
    assert lines[-1].startswith("/space/ ")
    assert lines[-1].endswith(buf.text)
