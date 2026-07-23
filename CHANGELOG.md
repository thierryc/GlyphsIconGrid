# Changelog

## 0.1.0 — 2026-07-23

First public release.

- Draws a fixed icon-construction canvas with square grid cells, concentric circles, radial spokes, live-area frames, and common icon keylines.
- Uses a cell-centered `odd` grid by default and supports an optional line-centered `even` mode.
- Supports one per-master `IconGrid.gridSize` value for both square-cell size and circular spacing; the recommended 1000-UPM starting values are `34` for Regular and `72` for Bold.
- Resolves validated custom parameters with master-over-font precedence and safe fallbacks.
- Provides non-snapping alignment feedback for editing and outline-creation tools.
- Supports Glyphs 3.5 and Glyphs 4 through a shared reporter bundle.
- Includes deterministic tests, dual-version static validation, release packaging, user documentation, and a guarded Glyphs MCP configuration skill.
