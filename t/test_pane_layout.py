# coding: utf-8

import pytest

from prompt_toolkit.utils import get_cwidth

from space.shell.pane import Record, anchor_step, clip_fragments, layout_rows, nrows


def rec(text, rigid=False, ephemeral=False, seq=0):
    return Record([("", text)], text, rigid, ephemeral, seq)


def texts(rows):
    return ["".join(f[1] for f in row) for row in rows]


def widths(rows):
    return [get_cwidth("".join(f[1] for f in row)) for row in rows]


WORDS = " ".join(f"w{i:02d}" for i in range(40))


def test_empty_log_is_all_blank_rows():
    rows = layout_rows([], 40, 6)
    assert len(rows) == 6
    assert texts(rows) == [""] * 6


def test_tiny_pane_returns_nothing():
    assert layout_rows([rec("hi")], 0, 10) == []
    assert layout_rows([rec("hi")], 10, 0) == []


def test_tail_is_pinned_to_the_bottom():
    rows = layout_rows([rec(f"line {i}") for i in range(10)], 40, 4)
    assert texts(rows) == ["line 6", "line 7", "line 8", "line 9"]


def test_prose_wraps_to_full_width_without_a_band():
    rows = layout_rows([rec(WORDS)], 40, 20)
    assert max(widths(rows)) <= 40
    assert "".join(texts(rows)).replace("  ", " ").strip().startswith("w00 w01")


def test_band_rows_are_clipped_and_padded_to_narrow():
    rows = layout_rows([rec(f"line {i}") for i in range(30)], 40, 10, band_w=12, band_h=3)
    assert widths(rows[:3]) == [28, 28, 28]
    assert all(w <= 40 for w in widths(rows[3:]))


def test_paragraph_below_the_band_keeps_the_full_width():
    # 4 wide rows in an 8 row pane starts at row 4, clear of a 3 row band
    assert nrows(WORDS, 40) == 4
    rows = layout_rows([rec(WORDS)], 40, 8, band_w=12, band_h=3)
    assert widths(rows)[:4] == [28, 28, 28, 0]
    assert all(28 < w <= 40 for w in widths(rows)[4:7])


def test_paragraph_starting_in_the_band_stays_narrow():
    # the same paragraph in a 6 row pane starts inside the band and so wraps
    # narrow for its whole height -- no staircase down the minimap edge
    rows = layout_rows([rec(WORDS)], 40, 6, band_w=12, band_h=3)
    assert nrows(WORDS, 28) == 6
    assert all(w <= 28 for w in widths(rows))


def test_narrow_choice_does_not_oscillate():
    # whatever width was chosen, re-running the layout must reproduce it
    records = [rec(WORDS), rec("tail")]
    first = layout_rows(records, 40, 12, band_w=12, band_h=4)
    assert texts(first) == texts(layout_rows(records, 40, 12, band_w=12, band_h=4))


def test_rigid_row_is_truncated_not_wrapped():
    bar = "|" + "=" * 70 + "|"
    rows = layout_rows([rec(bar, rigid=True)], 40, 5, band_w=12, band_h=3)
    assert widths(rows) == [28, 28, 28, 0, len(bar)]
    assert texts(rows)[4] == bar
    # in the band it gets cut at the narrow edge instead of taking extra rows
    rows = layout_rows([rec(bar, rigid=True)] * 3, 40, 3, band_w=12, band_h=3)
    assert widths(rows) == [28, 28, 28]


def test_narrow_has_a_floor_of_one():
    rows = layout_rows([rec("abcdef")], 10, 3, band_w=40, band_h=3)
    assert widths(rows) == [1, 1, 1]


def test_anchor_scrolls_the_view():
    records = [rec(f"line {i}") for i in range(10)]
    rows = layout_rows(records, 40, 3, anchor=(5, 0))
    assert texts(rows) == ["line 3", "line 4", "line 5"]


def test_anchor_past_the_end_clamps_to_the_tail():
    records = [rec(f"line {i}") for i in range(4)]
    assert texts(layout_rows(records, 40, 2, anchor=(99, 0))) == ["line 2", "line 3"]


def test_anchor_step_walks_rows_and_releases_at_the_tail():
    records = [rec(f"line {i}") for i in range(10)]
    assert anchor_step(records, None, -3, 40) == (6, 0)
    assert anchor_step(records, (6, 0), -1, 40) == (5, 0)
    assert anchor_step(records, (6, 0), 3, 40) is None
    assert anchor_step(records, None, -100, 40) == (0, 0)
    assert anchor_step([], None, -5, 40) is None


def test_anchor_step_counts_wrapped_rows():
    records = [rec(WORDS), rec("tail")]
    assert nrows(WORDS, 40) > 1
    assert anchor_step(records, None, -1, 40) == (0, nrows(WORDS, 40) - 1)


def test_clip_respects_double_width_glyphs():
    assert get_cwidth("漢字") == 4
    assert "".join(f[1] for f in clip_fragments([("", "漢字ab")], 3)) == "漢"
    assert "".join(f[1] for f in clip_fragments([("", "漢字ab")], 4)) == "漢字"


def test_styles_survive_wrapping():
    fragments = [("fg:red", "hello "), ("fg:blue", "world again")]
    rows = layout_rows([Record(fragments, "hello world again", False, False, 0)], 8, 4)
    assert [f for row in rows for f in row if f[1]] == [
        ("fg:red", "hello"),
        ("fg:blue", "world"),
        ("fg:blue", "again"),
    ]
