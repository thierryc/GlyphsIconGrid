# IconGrid parameter schema

The active master's valid value overrides the font's valid value. Missing, disabled, or invalid records fall through to the next scope and finally to the default.

Normal setup inherits the active master’s H stem and requires no `IconGrid.gridSize`. Leave every value unstored unless the user requests a different default. `gridMode` is the only setup parameter commonly needed.

| Name | What it controls | Accepted value | Default |
| --- | --- | --- | --- |
| `IconGrid.columns` | Count-based horizontal divisions when `gridSize` is unset; cell width is `width / columns`. | Integer `1–256` | `24` |
| `IconGrid.rows` | Count-based vertical divisions when `gridSize` is unset; cell height is `height / rows`. | Integer `1–256` | `24` |
| `IconGrid.gridSize` | Explicit square-cell size and circular-guide spacing. Overrides the active master’s preferred H stem. | Positive number in font units; no more than 256 cells across either canvas axis | Master H stem; otherwise use division and ring counts |
| `IconGrid.gridMode` | Whether a complete cell (`odd`) or intersecting grid lines (`even`) are centered on the construction axes. | `odd` or `even` | `odd` |
| `IconGrid.width` | Fixed construction-canvas width; not the glyph advance. | Positive number in font units | Font UPM, cap height, then `1000` |
| `IconGrid.height` | Fixed construction-canvas height. | Positive number in font units | Font UPM, cap height, then `1000` |
| `IconGrid.origin` | Horizontal advance anchoring and the initial vertical anchor of the fixed canvas. | One supported origin below | `bottom-center` |
| `IconGrid.baselineOffset` | Explicit vertical translation; positive moves the canvas down and replaces automatic cap-height centering. | Finite number in font units | `(height − capHeight) / 2` for the default origin when cap height is valid; otherwise `0` |
| `IconGrid.padding` | Explicit inset between the canvas edge and live circle/keyline area, measured in effective cells. Storing it replaces the automatic metric fit. | Non-negative number of grid cells | Unstored: live diameter is `(capHeight − baseline) / 0.8`, clamped to the canvas; `2` cells if cap height is unavailable |
| `IconGrid.majorEvery` | Emphasizes every Nth grid line; `0` removes major-line emphasis. | Integer `0–256` | `4` |
| `IconGrid.rings` | Count of evenly distributed circles when `gridSize` is unset; ignored when `gridSize` supplies exact spacing. | Integer `0–128` | `2` |
| `IconGrid.spokes` | Number of radial lines; `0` hides them. | Integer `0–360` | `8` |
| `IconGrid.showKeylines` | Visibility of circle, square, portrait, and landscape keylines. | Boolean | `true` |
| `IconGrid.color` | Construction-guide color. | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `#0A84FF` |
| `IconGrid.opacity` | Overall guide visibility. | Number, clamped to `0–1` | `0.28` |
| `IconGrid.alignmentHighlight` | Enables the stronger guide near an active drawing point or moving node; never enables snapping. | Boolean | `true` |
| `IconGrid.alignmentTolerance` | Maximum on-screen distance for the alignment cue; smaller is stricter. | Number `1–20` in screen points | `2` |

Supported origins:

- `bottom-left`, `bottom-center`, `bottom-right`
- `center-left`, `center`, `center-right`
- `top-left`, `top-center`, `top-right`

Use native JSON booleans with MCP. Human-entered Glyphs values also accept `on/off`, `yes/no`, `true/false`, and `1/0`.

A valid `IconGrid.gridSize` is the master’s explicit construction unit. It sets both square-cell size and the radial distance between up to two inner concentric circles, taking precedence over `columns`, `rows`, and `rings`. The circular keyline supplies the outer circle, so typical masters show two or three useful circles in total. Delete `gridSize` to restore the master-stem default. If there is no usable stem, the reporter restores the count-based settings. A valid explicit `columns`, `rows`, or `rings` value also intentionally selects the count-based model.

`IconGrid.gridMode = odd` centers one cell on the canvas centerlines and is the normal default. `IconGrid.gridMode = even` puts a grid border on each centerline. Keep this shared at font scope unless the arrangement intentionally differs by master.

## Generic weight-matched stem scaffold

For a new 1000-UPM icon set, start with these values in Glyphs’ master stems:

| Master | H stem |
| --- | ---: |
| Ultralight 100 | `25` |
| Thin 200 | `42` |
| Light 300 | `63` |
| Regular 400 | `84` |
| Medium 500 | `103` |
| Semibold 600 | `120` |
| Bold 700 | `135` |
| Extrabold 800 | `152` |
| Black 900 | `174` |

Scale proportionally for a different UPM and prefer measured H stems for existing outlines. Leave IconGrid font and master scopes empty unless the user intentionally wants to override the stem-derived default.
