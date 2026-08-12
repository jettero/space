# coding: utf-8

import pytest

from space.msg import BoxMessage, TextMessage

from t.shellexpect import ShellEnv

WIDTH, HEIGHT = 80, 25
PANE = HEIGHT - 2  # message pane; the rule and the input line take one row each
BAND_H = int(PANE * 0.4)
BAND_W = int(WIDTH * 0.4)
NARROW = WIDTH - BAND_W

PROSE = " ".join(f"word{i:02d}" for i in range(30))
BOX_RULE = "+" + "-" * 62 + "+"


def minimap_text(env):
    return ["".join(f[1] for f in row).rstrip() for row in env.shell.minimap.rows(WIDTH, PANE)]


def test_minimap_draws_the_owner_as_the_active_body(me, dd):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        dd.do("look")  # somebody else takes a turn, which clears our active flag
        assert not me.active
        env.screen()
        drawn = "\n".join(minimap_text(env))
    assert "@" in drawn, f"the owner should render as the active body, not {me.abbr!r}"


def test_the_inline_map_is_diverted_to_the_minimap(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        env.screen()
        assert [x for x in minimap_text(env) if x.strip()], "the minimap should have the map"
        records = env.shell.message_log.records
    assert not [
        r for r in records if r.rigid
    ], f"the map drawing should not also be in scrollback: {[r.plain for r in records]!r}"
    assert [r for r in records if r.plain.strip()], "look should still list what is nearby"


def test_no_minimap_when_the_shell_has_no_owner():
    with ShellEnv(WIDTH, HEIGHT) as env:
        for _ in range(12):
            env.shell.receive_message(TextMessage(PROSE))
        lines, _, _ = env.screen()
        assert env.shell.owner is None
        assert minimap_text(env) == []
    assert any(len(line) > NARROW for line in lines[:PANE]), "prose should use the whole width"


def test_minimap_lands_in_the_top_right_band(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        lines, _, _ = env.screen()
        drawn = minimap_text(env)
    assert len(drawn) == BAND_H
    assert [x for x in drawn if x.strip()], "the minimap rendered nothing at all"
    assert [line[NARROW:] for line in lines[:BAND_H]] == drawn
    assert all(x.startswith(" ") for x in drawn if x), "the minimap keeps a one column gap"
    assert not any(line[NARROW:].strip() for line in lines[BAND_H:PANE])


def test_prose_wraps_narrow_beside_the_minimap(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        for _ in range(12):
            env.shell.receive_message(TextMessage(PROSE))
        lines, _, _ = env.screen()
        drawn = minimap_text(env)
    assert [line[NARROW:] for line in lines[:BAND_H]] == drawn
    assert any(len(line) > NARROW for line in lines[BAND_H:PANE]), "below the band prose uses the whole width"


def test_rigid_box_is_truncated_in_the_band_and_whole_once_folded(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        env.shell.receive_message(BoxMessage("stats", ["x" * 60] * (BAND_H - 4)))
        for i in range(PANE - BAND_H):
            env.shell.receive_message(TextMessage(f"tick {i}"))
        lines, _, _ = env.screen()
        assert [line[:NARROW].rstrip() for line in lines[:BAND_H]].count(BOX_RULE[:NARROW]) == 3
        assert [line[NARROW:] for line in lines[:BAND_H]] == minimap_text(env)
        assert [line for line in lines[BAND_H:PANE] if line.startswith("tick ")]

        env.trigger("fold")
        lines, _, _ = env.screen()
        assert minimap_text(env) == []
    assert lines[0] == BOX_RULE
    assert [line for line in lines if line == "| " + "x" * 60 + " |"]


@pytest.mark.parametrize("key", ["fold", "fold-tab"])
def test_either_fold_key_folds_the_minimap(me, key):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        env.screen()
        assert [x for x in minimap_text(env) if x.strip()]
        env.trigger(key)
        assert not env.shell.minimap.visible
        assert minimap_text(env) == []
        env.trigger(key)
        assert [x for x in minimap_text(env) if x.strip()]


def test_refresh_key_repaints(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.receive_message(TextMessage("still here"))
        env.screen()
        env.trigger("refresh")
        lines, _, _ = env.screen()
    assert any("still here" in line for line in lines)


def test_slash_minimap_folds_and_unfolds(me):
    with ShellEnv(WIDTH, HEIGHT) as env:
        env.shell.owner = me
        env.shell.do_step("look")
        env.screen()
        assert env.shell.minimap.visible
        env.shell.do_step("/minimap off")
        assert minimap_text(env) == []
        env.shell.do_step("/mm on")
        lines, _, _ = env.screen()
        assert [line[NARROW:] for line in lines[:BAND_H]] == minimap_text(env)
        assert [x for x in minimap_text(env) if x.strip()]
