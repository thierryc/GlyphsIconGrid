# Custom parameter reference

Resolution is field-by-field: the active master’s valid `IconGrid.*` value wins, then the font’s valid value, then the documented default. Disabled parameters are ignored. Invalid values fall back safely and emit one deduplicated Macro Panel warning per plug-in session.

| Parameter | Accepted value | Default |
| --- | --- | --- |
| `IconGrid.columns` | Integer 1–256 | `24` |
| `IconGrid.rows` | Integer 1–256 | `24` |
| `IconGrid.gridSize` | Positive number in font units; must keep each canvas axis within 256 cells | Unset; use the division and ring counts |
| `IconGrid.gridMode` | `odd` or `even` | `odd` |
| `IconGrid.height` | Positive number | Font UPM, then active master cap height, then `1000` |
| `IconGrid.width` | Positive number | Font UPM, then active master cap height, then `1000` |
| `IconGrid.origin` | One of the nine names below | `bottom-center` |
| `IconGrid.baselineOffset` | Finite number in font units; positive moves the canvas down | `(height − xHeight) / 2` for the default origin; otherwise `0` |
| `IconGrid.padding` | Non-negative grid-cell count | `2` |
| `IconGrid.majorEvery` | Integer 0–256; `0` disables major lines | `4` |
| `IconGrid.rings` | Integer 0–128 | `floor(min(columns, rows) / 2 − padding)` |
| `IconGrid.spokes` | Integer 0–360 | `8` |
| `IconGrid.showKeylines` | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.color` | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `#0A84FF` |
| `IconGrid.opacity` | Number, clamped to 0–1 | `0.28` |
| `IconGrid.alignmentHighlight` | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.alignmentTolerance` | Number from 1–20, measured in screen points | `2` |

Supported origins are `bottom-left`, `bottom-center`, `bottom-right`, `center-left`, `center`, `center-right`, `top-left`, `top-center`, and `top-right`.

With no size or division overrides, the plug-in uses the font UPM for both dimensions and 24 divisions on each axis. This produces the square construction canvas and square cells expected for icons. Horizontally, `bottom-center` centers the canvas on the glyph advance. Its automatic baseline offset places the canvas center halfway between y=0 and the active master’s x-height. If x-height is unavailable, the safe baseline-offset fallback is `0`. Explicit parameters are preserved and can intentionally create another layout.

A valid `IconGrid.gridSize` is the master’s construction unit. It sets both x/y square-cell spacing and the radial distance between concentric circles. It takes precedence over `IconGrid.columns`, `IconGrid.rows`, and `IconGrid.rings`. Delete it to return to the count-based settings. `IconGrid.padding` remains a count of the effective grid cells.

Set `IconGrid.gridSize` on each master and leave font scope empty when the built-in appearance and guide defaults are suitable. For a 1000-UPM icon set, use `34` on Regular and `72` on Bold. Scale those values proportionally for another UPM or replace them with the actual construction/stroke unit of each master.

`IconGrid.gridMode` controls the grid phase around the canvas center in both directions. The default `odd` mode centers one complete cell on the horizontal and vertical construction axes, so neither axis is itself a grid line. In `even` mode, a vertical and horizontal grid line coincide with the two construction axes. Major-line cadence remains symmetric around the center in both modes. The setting follows the same master-over-font resolution as every other parameter.

`IconGrid.width` and `IconGrid.height` define a fixed construction canvas. The horizontal part of the origin aligns the canvas to the active layer's advance: `left` puts its left edge at x=0, `center` puts its center at half the advance, and `right` puts its right edge at the advance. The grid is never stretched to match the advance. The vertical part establishes the unshifted anchor; `IconGrid.baselineOffset` then translates the canvas downward. An explicit baseline offset replaces the automatic x-height-centered value.

Grid cadence is measured outwards from the translated canvas center, not from the canvas minimum or y=0. Circular guides use the same center.

The background grid extends by the same whole number of cells on all four sides. Under the square defaults, that keeps the background square; explicit non-square dimensions or division counts intentionally remain non-square. The extension targets at least one complete cell past the active master’s cap-height/ascender and descender extents, subject to a six-cell-per-side safety cap. This provides modest room for exceptional artwork above, below, left, or right without filling the Edit view. The canvas and live-area frames, rings, spokes, and keylines remain inside their configured bounds.

`IconGrid.padding` is measured separately in x and y cells. It is clamped before the live area can collapse. Geometry counts are bounded to keep redraw work predictable.

The fixed blue default keeps the icon construction grid visually distinct from Glyphs' metric and user guides. Set `IconGrid.color` when a different contrast is needed.

When alignment highlighting is enabled, Draw, Rectangle/Square, and Circle provide a live hover cue whenever their pointer is within `alignmentTolerance` of a construction guide. During Rectangle or Circle construction, the native preview endpoint takes precedence because the shape's nodes do not exist until mouse-up. Edit behavior is separate: a selected `GSNode` must actually move during a native drag. Pencil contributes its last point only after an active stroke records movement, and Annotation never activates the cue. A lasso, static Edit selection, or passive Edit pointer cannot activate it. The default two-screen-point threshold is intentionally strict, and it is divided by the current zoom scale so it remains constant on screen. At crossings, all matching guides highlight together. Alignment state is temporary and is never written to the font.
