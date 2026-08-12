# coding: utf-8

import pytest

from space.msg import TextMessage

from t.shellexpect import ShellEnv

WIDTH, HEIGHT = 80, 25
PANE = HEIGHT - 2


def test_slash_map_swaps_the_pane_and_escape_puts_it_back(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("look")
        shell.receive_message(TextMessage("a quiet corner of the station"))
        lines, _, _ = env.screen()
        assert shell.message_window.content is shell.pane_control
        assert any("a quiet corner" in line for line in lines)

        shell.do_step("/map")
        lines, _, _ = env.screen()
        assert shell.full_map
        assert shell.message_window.content is shell.map_control
        assert not any("a quiet corner" in line for line in lines)
        assert lines[PANE - 1].startswith(f" you {tuple(me.location.pos)}")

        env.trigger("escape")
        lines, _, _ = env.screen()
        assert not shell.full_map
        assert shell.message_window.content is shell.pane_control
        assert any("a quiet corner" in line for line in lines)


def test_the_full_map_is_drawn_once_and_panned_by_scrolling(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("look")
        shell.do_step("/map")
        env.screen()
        buffer = shell.map_buffer
        assert len(buffer) == me.vmap.bounds.YY, "the buffer is the whole line-of-sight extent"
        assert "@" in "".join(f[1] for row in buffer for f in row), "drawn from the owner's viewpoint"

        home = shell.map_pan
        for name, delta in (("left", (-1, 0)), ("right", (1, 0)), ("up", (0, -1)), ("down", (0, 1))):
            shell.map_pan = (5, 5)
            env.trigger(name)
            assert shell.map_pan == (5 + delta[0], 5 + delta[1]), name
        assert shell.map_buffer is buffer, "panning must not redraw"

        shell.map_pan = home
        env.screen()
        assert shell.map_buffer is buffer


def test_panning_clamps_to_the_buffer(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("look")
        shell.do_step("/map")
        shell.map_pan = (0, 0)
        env.trigger("left")
        env.trigger("up")
        assert shell.map_pan == (0, 0)


def test_chevrons_mark_buffer_beyond_the_viewport(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("look")
        shell.do_step("/map")
        env.screen()
        shell.map_pan = (0, 0)
        shell.map_buffer = [[("", "x" * 200)] for _ in range(60)]
        lines, _, _ = env.screen()
        assert lines[(PANE - 1) // 2].endswith("►")
        assert "▼" in lines[PANE - 2]

        shell.map_pan = (150, 40)
        lines, _, _ = env.screen()
        assert lines[(PANE - 1) // 2].startswith("◄")
        assert "▲" in lines[0]


def test_slash_map_on_and_off_are_explicit(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("look")
        shell.do_step("/map off")
        assert not shell.full_map
        shell.do_step("/map on")
        assert shell.full_map
        shell.do_step("/map on")
        assert shell.full_map
        shell.do_step("/map")
        assert not shell.full_map


def config_echo(env):
    return [r.plain for r in env.shell.message_log.records if " = " in r.plain]


def test_slash_config_lists_shows_and_sets(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("/config")
        assert config_echo(env) == ["maps.inline = False", "maps.minimap = True"]

        shell.do_step("/config maps.inline")
        assert config_echo(env)[-1] == "maps.inline = False"

        shell.do_step("/config maps.inline = on")
        assert shell.config["maps.inline"] is True
        assert config_echo(env)[-1] == "maps.inline = True"

        shell.do_step("/config maps.minimap = off")
        assert shell.config["maps.minimap"] is False

        shell.do_step("/config maps.nonsense = 3")
        assert "maps.nonsense" not in shell.config
        assert env.shell.message_log.records[-1].plain == "unknown config key: maps.nonsense"


def test_slash_mm_swaps_the_two_map_settings(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        assert (shell.config["maps.minimap"], shell.config["maps.inline"]) == (True, False)
        shell.do_step("/mm")
        assert (shell.config["maps.minimap"], shell.config["maps.inline"]) == (False, True)
        shell.do_step("/mm")
        assert (shell.config["maps.minimap"], shell.config["maps.inline"]) == (True, False)
        shell.do_step("/mm off")
        assert (shell.config["maps.minimap"], shell.config["maps.inline"]) == (False, True)


def test_minimap_and_inline_are_independently_settable(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("/config maps.inline = true")
        shell.do_step("look")
        assert [r for r in shell.message_log.records if r.rigid], "inline on puts the drawing in scrollback"
        assert [x for x in shell.minimap.rows(WIDTH, PANE) if x], "and the minimap still has it too"


def test_inline_only_leaves_the_band_empty(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        shell = env.shell
        shell.owner = me
        shell.do_step("/mm off")
        shell.do_step("look")
        assert [r for r in shell.message_log.records if r.rigid]
        assert shell.minimap.rows(WIDTH, PANE) == []


def test_unknown_slash_command_does_not_need_an_owner():
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.do_step("/nope")
        assert env.shell.message_log.records[-1].plain == "unknown shell command: /nope"


def test_full_map_before_any_map_has_arrived_says_so():
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.do_step("/map")
        lines, _, _ = env.screen()
    assert lines[0] == "no map yet — look around first"
