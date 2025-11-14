import pytest

from space.msg import TextMessage

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


def test_tab_completion_inserts_common_prefix():
    with ShellEnv() as env:
        doc, completions, extra = find_completion_extension(env)
        buf = env.apply_completions(doc, completions)
        env.trigger("tab")
        assert buf.text == doc.text + extra
        lines, _, _ = env.render_lines()
    assert lines[-1].startswith("/space/ ")
    assert lines[-1].endswith(buf.text)
