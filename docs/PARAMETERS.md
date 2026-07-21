# Custom parameter reference

Resolution is field-by-field: the active master’s valid `IconGrid.*` value wins, then the font’s valid value, then the documented default. Disabled parameters are ignored. Invalid values fall back safely and emit one deduplicated Macro Panel warning per plug-in session.

| Parameter | Accepted value | Default |
| --- | --- | --- |
| `IconGrid.columns` | Integer 1–256 | `24` |
| `IconGrid.rows` | Integer 1–256 | `24` |
| `IconGrid.height` | Positive number | Active master cap height, then font UPM, then `1000` |
| `IconGrid.origin` | One of the nine names below | `bottom-left` |
| `IconGrid.padding` | Non-negative grid-cell count | `2` |
| `IconGrid.majorEvery` | Integer 0–256; `0` disables major lines | `4` |
| `IconGrid.rings` | Integer 0–128 | `floor(min(columns, rows) / 2 − padding)` |
| `IconGrid.spokes` | Integer 0–360 | `8` |
| `IconGrid.showKeylines` | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.color` | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `accent` |
| `IconGrid.opacity` | Number, clamped to 0–1 | `0.28` |

Supported origins are `bottom-left`, `bottom-center`, `bottom-right`, `center-left`, `center`, `center-right`, `top-left`, `top-center`, and `top-right`.

The named origin places glyph coordinate `(0, 0)` at that point of a canvas whose width is the active layer width and whose height is `IconGrid.height`. Grid cadence is measured outwards from `(0, 0)`, not from the canvas minimum. Circular guides remain centered on the canvas.

`IconGrid.padding` is measured separately in x and y cells. It is clamped before the live area can collapse. Geometry counts are bounded to keep redraw work predictable.
