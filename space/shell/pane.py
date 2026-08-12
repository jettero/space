# coding: utf-8

"""
Pure text-pane geometry: no containers, no window, no application.

A pane is a rectangle of `height` rows by `width` display columns holding the
tail of a message log.  A "band" (the minimap) may occupy the top `band_h` rows
of the rightmost `band_w` columns; prose that lands in the band wraps into the
remaining `narrow` columns, rigid rows are clipped there instead.

Fragments are prompt_toolkit (style, text) tuples, measured with its own
get_cwidth/fragment_list_width so a slice here lands on the same column the
renderer will put it in.  Nothing here knows what a style string means.
"""

from collections import namedtuple

from prompt_toolkit.formatted_text.utils import fragment_list_width
from prompt_toolkit.utils import get_cwidth

Record = namedtuple("Record", ["fragments", "plain", "rigid", "ephemeral", "seq"])


def wrap_points(plain: str, width: int) -> list:
    """
    Word-wrap plain text to width display columns and return one (start, end)
    index pair per resulting row.  Breaks at the last space that fits; falls
    back to a hard break when a single word is wider than the pane.  The
    result is never empty -- an empty string wraps to a single empty row.
    """

    if width < 1 or not plain:
        return [(0, len(plain))]
    points = list()
    i, n = 0, len(plain)
    while i < n:
        j, w, space = i, 0, None
        while j < n and w + get_cwidth(plain[j]) <= width:
            w += get_cwidth(plain[j])
            if plain[j] == " ":
                space = j
            j += 1
        if j >= n:
            points.append((i, n))
            break
        if space is not None and space > i:
            points.append((i, space))
            i = space + 1
        else:
            points.append((i, max(j, i + 1)))
            i = max(j, i + 1)
    return points or [(0, 0)]


def nrows(plain: str, width: int) -> int:
    """Number of display rows plain text occupies when wrapped to width."""

    return len(wrap_points(plain, width))


def slice_fragments(fragments, start: int, end: int) -> list:
    """
    Cut a fragment list down to the plain-text index range [start, end),
    preserving each surviving fragment's style.
    """

    out = list()
    pos = 0
    for frag in fragments:
        nxt = pos + len(frag[1])
        if nxt > start and pos < end:
            out.append((frag[0], frag[1][max(0, start - pos) : end - pos]))
        pos = nxt
        if pos >= end:
            break
    return out


def split_fragments(fragments, col: int) -> tuple:
    """
    Cut a fragment row at display column col and return (head, tail).

    Every input fragment appears in both halves, possibly empty, so trailing
    style resets survive either side.  A double-width character that would
    straddle the cut goes to the tail; pad_fragments fills the column it
    vacates.
    """

    head, tail, used = list(), list(), 0
    for frag in fragments:
        take = ""
        for c in frag[1]:
            if used + (w := get_cwidth(c)) > col:
                break
            take += c
            used += w
        head.append((frag[0], take))
        tail.append((frag[0], frag[1][len(take) :]))
    return head, tail


def clip_fragments(fragments, width: int) -> list:
    """The part of a fragment row before display column width."""

    return split_fragments(fragments, width)[0]


def drop_fragments(fragments, col: int) -> list:
    """The part of a fragment row at or beyond display column col."""

    return split_fragments(fragments, col)[1]


def pad_fragments(fragments, width: int) -> list:
    """Right-pad a fragment row with spaces so it occupies exactly width columns."""

    out = list(fragments)
    if (d := width - fragment_list_width(out)) > 0:
        out.append(("", " " * d))
    return out


def splice_fragments(fragments, col: int, text: str) -> list:
    """Overwrite display columns [col, col+width(text)) of a row with text."""

    return (
        pad_fragments(clip_fragments(fragments, col), col) + [("", text)] + drop_fragments(fragments, col + get_cwidth(text))
    )


def record_height(rec: Record, width: int) -> int:
    """Display rows one log record occupies: rigid rows never wrap."""

    return 1 if rec.rigid else nrows(rec.plain, width)


def record_rows(rec: Record, width: int) -> list:
    """
    Render one log record into display rows.  Rigid records are always a
    single (unwrapped, later clipped) row; everything else word-wraps.
    """

    if rec.rigid:
        return [list(rec.fragments)]
    return [slice_fragments(rec.fragments, s, e) for s, e in wrap_points(rec.plain, width)]


def layout_rows(records, width: int, height: int, band_w: int = 0, band_h: int = 0, anchor=None) -> list:
    """
    Lay records out into exactly height rows of width columns and return them
    as a list of fragment lists, top row first.

    anchor is None to pin the bottom row to the end of the log, or an
    (index, wrap offset) pair naming the record row that should be the bottom
    row of the pane.  Rows are built bottom-up so the tail is always exact;
    the top is padded with blank rows when the log is short.

    band_w/band_h describe a rectangle reserved in the top-right corner.  A
    record whose first row falls inside those top band_h rows is wrapped to
    the narrow width for its whole height (so a paragraph reads as one
    column, not a staircase), and the band rows are clipped and padded to
    exactly the narrow width so the caller can append band content at a known
    column.  Re-wrapping narrower only makes a record taller, which only
    pushes its top row further up, so the narrow decision never oscillates.
    """

    if width < 1 or height < 1:
        return []
    banded = band_w > 0 and band_h > 0
    narrow = max(1, width - band_w) if banded else width

    out = list()
    idx = len(records) - 1 if anchor is None else min(anchor[0], len(records) - 1)
    limit = None if anchor is None else anchor[1]

    def height_of(rec, w):
        return record_height(rec, w) if limit is None else min(record_height(rec, w), limit + 1)

    while idx >= 0 and len(out) < height:
        rec = records[idx]
        w, n = width, height_of(rec, width)
        if banded and height - len(out) - n < band_h:
            w, n = narrow, height_of(rec, narrow)
        out[:0] = record_rows(rec, w)[:n]
        limit = None
        idx -= 1

    if len(out) > height:
        out = out[len(out) - height :]
    out = [[] for _ in range(height - len(out))] + out

    if banded:
        for r in range(min(band_h, height)):
            out[r] = pad_fragments(clip_fragments(out[r], narrow), narrow)
    return out


def anchor_step(records, anchor, delta: int, width: int):
    """
    Move an (index, wrap offset) scroll anchor by delta display rows and
    return the new anchor, or None when the move lands on (or past) the last
    row of the log -- None means "follow the tail".

    Row counts are computed at the full pane width; a band changes wrapping
    for at most a few rows and is not worth the second pass here.
    """

    counts = [record_height(r, width) for r in records]
    if not counts:
        return None
    total = sum(counts)
    if anchor is None:
        row = total - 1
    else:
        i = max(0, min(anchor[0], len(counts) - 1))
        row = sum(counts[:i]) + min(anchor[1], counts[i] - 1)
    row = max(0, min(total - 1, row + delta))
    if row == total - 1:
        return None
    for i, c in enumerate(counts):
        if row < c:
            return (i, row)
        row -= c
    return None
