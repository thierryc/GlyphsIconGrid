# Custom parameter reference

Resolution is field-by-field: the active master’s valid `IconGrid.*` value wins, then the font’s valid value, then the documented default. Disabled parameters are ignored. Invalid values fall back safely and emit one deduplicated Macro Panel warning per plug-in session.

| Parameter | Accepted value | Default |
| --- | --- | --- |
| `IconGrid.columns` | Integer 1–256 | `24` |
| `IconGrid.rows` | Integer 1–256 | `24` |
| `IconGrid.height` | Positive number | Active master cap height, then font UPM, then `1000` |
| `IconGrid.width` | Positive number | `1.5 × font UPM` (or `1500`) |
| `IconGrid.origin` | One of the nine names below | `bottom-left` |
| `IconGrid.baselineOffset` | Finite number in font units; positive moves the canvas down | `0` |
| `IconGrid.padding` | Non-negative grid-cell count | `2` |
| `IconGrid.majorEvery` | Integer 0–256; `0` disables major lines | `4` |
| `IconGrid.rings` | Integer 0–128 | `floor(min(columns, rows) / 2 − padding)` |
| `IconGrid.spokes` | Integer 0–360 | `8` |
| `IconGrid.showKeylines` | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.color` | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `accent` |
| `IconGrid.opacity` | Number, clamped to 0–1 | `0.28` |
| `IconGrid.hoverHighlight` | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.hoverTolerance` | Number from 1–20, measured in screen points | `5` |

Supported origins are `bottom-left`, `bottom-center`, `bottom-right`, `center-left`, `center`, `center-right`, `top-left`, `top-center`, and `top-right`.

`IconGrid.width` and `IconGrid.height` define a fixed construction canvas. The horizontal part of the origin aligns the canvas to the active layer's advance: `left` puts its left edge at x=0, `center` puts its center at half the advance, and `right` puts its right edge at the advance. The grid is never stretched to match the advance. The vertical part anchors the bottom, center, or top at y=0. `IconGrid.baselineOffset` then translates the canvas downward, making the font baseline an internal construction axis when the value is positive.

Grid cadence is measured outwards from the chosen horizontal anchor and from y=0, not from the canvas minimum. Circular guides remain centered on the translated fixed canvas.

`IconGrid.padding` is measured separately in x and y cells. It is clamped before the live area can collapse. Geometry counts are bounded to keep redraw work predictable.

When hover highlighting is enabled, every visible guide within `hoverTolerance` of the pointer is highlighted. The tolerance is divided by the current zoom scale, so it remains constant on screen. At crossings, all matching guides highlight together. Hover state is temporary and is never written to the font.
