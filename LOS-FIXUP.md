## LOS Render Fix

- Goal: keep physics-grade LOS for parser/logic while clipping ASCII output to a
  manageable viewport.
- Problem: full LOS draws overwhelm the terminal; cropping risks hiding
  interactable tiles.
- Approach:
  - Continue computing the full visible set for LOS MapView so parser remains
    unchanged.
  - Add a secondary MapView (≈30 m radius) for rendering; it reuses the same
    visibility data but limits the drawn window.
  - Modify MapView rendering to detect when visible tiles extend past the render
    window and emit directional continuation glyphs (← → ↑ ↓) right next to
    visible blue-background tiles. (The blue background indicates line of site.)
  - Ensure the continuation glyphs inherit the “visible” styling (blue) so
    players see they’re touching genuine LOS cells.
  - Parser keeps referencing the full MapView; UI swaps in the cropped
    MapView+indicators for display.
