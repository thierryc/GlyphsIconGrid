# Changelog

## 0.2.0 — 2026-08-06

- Centers the complete construction system on each active master's native,
  unfiltered Mid Height metric when one has a usable position.
- Preserves baseline-to-cap-height midpoint centering when Mid Height is
  unavailable and keeps explicit `IconGrid.baselineOffset` values authoritative.
- Keeps the live/keyline diameter cap-height-derived while moving its center
  with the master metric, with matching Glyphs 3.5 and Glyphs 4 coverage.

## 0.1.1 — 2026-07-27

- Prevents hover feedback from invalidating every Glyphs Edit and Preview view, preserving Glyphs 4 shape-tool previews during native drags.
- Caches hover geometry and guide catalogs, rejects invalid scales, batches alignment hit testing, and suppresses cues above 64 moving nodes to protect main-app responsiveness.

## 0.1.0 — 2026-07-23

First public release.

- Draws a fixed icon-construction canvas with square grid cells, concentric circles, radial spokes, live-area frames, and common icon keylines.
- Uses a cell-centered `odd` grid by default and supports an optional line-centered `even` mode.
- Uses the active master’s H stem for square-cell size and circular spacing, with explicit `IconGrid.gridSize` overrides when needed; the generic 1000-UPM icon scaffold starts at `84` for Regular and `135` for Bold.
- Centers the construction system vertically halfway between the baseline and cap height.
- Fits the unstored live/keyline diameter to `capHeight / 0.8`, making the landscape keyline span exactly from baseline to cap height.
- Extends the background grid by at least four cells per side and limits stem-spaced construction to two inner circles.
- Resolves validated custom parameters with master-over-font precedence and safe fallbacks.
- Provides non-snapping alignment feedback for editing and outline-creation tools.
- Supports Glyphs 3.5 and Glyphs 4 through a shared reporter bundle.
- Includes deterministic tests, dual-version static validation, release packaging, user documentation, and a guarded Glyphs MCP configuration skill.
