# IconGrid parameter schema

The active master's valid value overrides the font's valid value. Missing, disabled, or invalid records fall through to the next scope and finally to the default.

| Name | Accepted value | Default |
| --- | --- | --- |
| `IconGrid.columns` | Integer `1–256` | `24` |
| `IconGrid.rows` | Integer `1–256` | `24` |
| `IconGrid.gridSize` | Positive number in font units; no more than 256 cells across either canvas axis | Unset; use the division and ring counts |
| `IconGrid.gridMode` | `odd` or `even` | `odd` |
| `IconGrid.width` | Positive number in font units | Font UPM, cap height, then `1000` |
| `IconGrid.height` | Positive number in font units | Font UPM, cap height, then `1000` |
| `IconGrid.origin` | One supported origin below | `bottom-center` |
| `IconGrid.baselineOffset` | Finite number in font units | `(height − xHeight) / 2` for the default origin when x-height is valid; otherwise `0` |
| `IconGrid.padding` | Non-negative number of grid cells | `2` |
| `IconGrid.majorEvery` | Integer `0–256`; `0` disables major lines | `4` |
| `IconGrid.rings` | Integer `0–128` | `floor(min(columns, rows) / 2 − padding)` |
| `IconGrid.spokes` | Integer `0–360` | `8` |
| `IconGrid.showKeylines` | Boolean | `true` |
| `IconGrid.color` | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `#0A84FF` |
| `IconGrid.opacity` | Number, clamped to `0–1` | `0.28` |
| `IconGrid.alignmentHighlight` | Boolean | `true` |
| `IconGrid.alignmentTolerance` | Number `1–20` in screen points | `2` |

Supported origins:

- `bottom-left`, `bottom-center`, `bottom-right`
- `center-left`, `center`, `center-right`
- `top-left`, `top-center`, `top-right`

Use native JSON booleans with MCP. Human-entered Glyphs values also accept `on/off`, `yes/no`, `true/false`, and `1/0`.

A valid `IconGrid.gridSize` is the master’s single construction unit. It sets both square-cell size and the radial distance between concentric circles, taking precedence over `columns`, `rows`, and `rings`. Delete it to restore the count-based settings.

`IconGrid.gridMode = odd` centers one cell on the canvas centerlines and is the normal default. `IconGrid.gridMode = even` puts a grid border on each centerline. Keep this shared at font scope unless the arrangement intentionally differs by master.

## Recommended weight-matched master grid

For a 1000-UPM icon set, start with these values at master scope:

| Master | Grid size |
| --- | ---: |
| Regular | `34` |
| Bold | `72` |

Scale proportionally for a different UPM when the user has not supplied a construction unit. Leave font scope empty unless the user intentionally wants to override a built-in default.
