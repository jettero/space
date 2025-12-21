## LOS Render Fix

- Goal: keep physics-grade LOS for parser/logic while clipping ASCII output to a
  manageable viewport.
- Problem: full LOS draws overwhelm the terminal; cropping risks hiding
  interactable tiles.
- Approach:
  - Continue computing the full visible set for LOS MapView so parser remains
    unchanged.
  - Add a secondary MapView (≈30 m radius) for rendering; it reuses the same
    visibility data but limits the drawn window.
  - Modify MapView rendering to detect when visible tiles extend past the render
    window and emit directional continuation glyphs (← → ↑ ↓) right next to
    visible blue-background tiles. (The blue background indicates line of site.)
  - Ensure the continuation glyphs inherit the "visible" styling (blue) so
    players see they're touching genuine LOS cells.
  - Parser keeps referencing the full MapView; UI swaps in the cropped
    MapView+indicators for display.

## Previous Attempt - Failed Implementation

### What Was Tried
- Added `render_radius` parameter to `Map.visicalc_submap(whom, maxdist=None, render_radius=None)`
- When render_radius is set, created centered Bounds instead of tight-fitting bounds
- Added `_render_radius` to MapView.__init__() to track render mode
- Added `_detect_continuation()` method to check for visible cells beyond bounds
- Added `_inject_continuation_glyphs()` method to insert arrows into text_drawing array
- Modified `colorized_text_drawing` to call continuation helpers
- Changed `Living.do_look()` to pass `render_radius=30`

### Why It Failed
Implementation did not work correctly (specific failure mode not documented).

### Key Architectural Insights (Still Valid)
1. **Parser must remain unchanged** - uses `visicalc_submap()` at `space/parser.py:32`
2. **LOS calculation is separate from rendering** - `visicalc(whom)` marks cells with "can_see" tag
3. **MapView already supports bounds** - `MapView(map, bounds=...)` clips viewport
4. **Blue background is ANSI color 17** - applied in `colorized_text_drawing` line 120, 143-144
5. **Existing visicalc_submap has maxdist param** - for visibility range limiting (different from render radius)
6. **Bounds class takes positional args** - `Bounds(x, y, X, Y)` not keyword args
7. **Rendering pipeline**: `Map.cells → _text_drawing() → colorized_text_drawing → MapMessage`

### Critical Issues to Address in Next Attempt
1. **Text rendering timing** - arrows may need to be injected at different point in pipeline
2. **Coordinate mapping** - text_drawing uses relative coords, continuation detection uses absolute
3. **ANSI code handling** - text_drawing elements contain color codes, may break arrow injection
4. **Edge detection accuracy** - checking bounds.y/Y/x/X against cell.pos may have off-by-one errors
5. **MapView filtering interaction** - `_filter=True` hides non-visible cells, may conflict with continuation
6. **Cache invalidation** - `visicalc_submap` is `@lru_cache`'d, new params affect cache keys
7. **Render vs parser flow** - need clear separation so parser gets full LOS, render gets clipped

### Architecture Notes
- `Map.visicalc(whom, maxdist)` - computes LOS, marks cells with "can_see" tag
- `Map.visicalc_submap(whom, maxdist)` - returns MapView with tight bounds around visible cells
- `MapView.cells` - filters cells based on `_filter` parameter
- `MapView._text_drawing()` - converts cells to 2D array of strings
- `Map.colorized_text_drawing` - adds ANSI color codes to text_drawing
- `MapMessage(mapview)` - renders map for display via `mapview.colorized_text_drawing`

### Test Environment
- `asset/station1.map` - wagon-wheel torus, good for testing LOS on large open areas
- `./lrun-shell.py asset/station1.map` - loads map with test objects (DO NOT AUTOMATE)
- Full test suite passes (802 tests) but visual rendering was incorrect
