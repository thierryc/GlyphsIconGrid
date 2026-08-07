# Custom parameter guide

Most users need **no IconGrid custom parameter**. When the active master has stem metrics, the plug-in uses its capital-H horizontal stem as the exact square-cell size and circular-guide spacing. A named H vertical stem is the fallback when no H horizontal stem is available.

Leave font scope empty and leave every other `IconGrid.*` parameter unset unless you intentionally want to change a default. The plug-in supplies the canvas size, centering, guides, color, opacity, and alignment behavior automatically.

Vertical centering also needs no custom parameter. The reporter uses the active
master's first usable, unfiltered native Mid Height position and ignores its
overshoot. When that metric is unavailable or invalid, it falls back to the
baseline/cap-height midpoint. Store `IconGrid.baselineOffset` only for an
intentional override.

For the default Glyphs baseline at `0` and cap height at `700`, the number of stem-sized cells in that span is:

```text
x = (cap height − baseline) / H stem
```

`x` is allowed to be fractional so the grid remains an exact match for the weight-specific stem.

The live circle and Material keylines use a separate metric-derived size:

```text
live diameter = (cap height − baseline) / 0.8
```

At the default 700-unit cap height, the live diameter is 875 units. The
landscape keyline is 80% of that diameter, so its lower and upper edges land on
baseline and cap height when the construction center is their midpoint. A
distinct Mid Height moves the keyline without changing its size. Store
`IconGrid.padding` only to replace this automatic fit with a cell-based inset.

## What should I set?

| Goal | Set |
| --- | --- |
| Match the grid to each master’s H stem | Define the master stems in Glyphs; set no IconGrid parameter |
| Center on each master's Mid Height | Define an unfiltered native Mid Height in Glyphs; set no IconGrid parameter |
| Override the stem-derived size | `IconGrid.gridSize` on the relevant master |
| Put grid lines on the horizontal and vertical center axes | `IconGrid.gridMode = even`; otherwise leave the default `odd` |
| Change appearance or guide visibility | Only the relevant optional parameter below |
| Build a custom count-based or non-standard canvas | Use the advanced parameters below and leave `gridSize` unset |

## Normal setup

| Parameter | What it controls | Accepted value | Default |
| --- | --- | --- | --- |
| `IconGrid.gridSize` | Explicit square-cell size and circular-guide spacing. It overrides the active master’s H stem. | Positive number in font units; the canvas may not exceed 256 cells on either axis | Active master H stem; otherwise use the count-based defaults |
| `IconGrid.gridMode` | Grid phase at the canvas center. `odd` centers a complete cell on the axes; `even` places grid lines on the axes. | `odd` or `even` | `odd` |

When `gridSize` is valid, it takes precedence over `columns`, `rows`, and `rings`. Those values may remain stored, but they do not control cell or circle spacing until `gridSize` is removed.

Without an explicit `gridSize`, a valid `columns`, `rows`, or `rings` parameter intentionally selects the advanced count-based model and suppresses the automatic stem size.

### Generic 1000-UPM starting scaffold

Use measured master stems whenever possible. For a new icon family, the report’s Regular-relative scaffold provides these starting values:

| Weight | H stem |
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

Enter the chosen values under **File → Font Info → Masters → Stems**. They are an empirical first pass, not a substitute for measuring finished outlines.

## Optional guide, appearance, and interaction controls

These settings already have useful defaults. Add only the setting you want to change.

| Parameter | What it controls | Accepted value | Default |
| --- | --- | --- | --- |
| `IconGrid.padding` | Explicit inset, measured in effective grid cells, between the construction-canvas edge and the live circle/keyline area. Storing it replaces the automatic metric fit. | Non-negative number of cells | Unstored: live diameter is `(capHeight − baseline) / 0.8`, clamped to the canvas; `2` cells when cap height is unavailable |
| `IconGrid.majorEvery` | Emphasizes every Nth grid line, counted symmetrically from the center. Set `0` for no major lines. | Integer `0–256` | `4` |
| `IconGrid.spokes` | Number of radial lines through the circular construction area. Set `0` to hide them. | Integer `0–360` | `8` |
| `IconGrid.showKeylines` | Shows or hides the circle, square, portrait, and landscape icon keylines. | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.color` | Color of the Icon Grid, kept separate from Glyphs metric and user guides. | `accent`, `grid`, `label`, `separator`, or `#RRGGBB` | `#0A84FF` |
| `IconGrid.opacity` | Overall visibility of the construction system. `0` is invisible and `1` is fully opaque. | Number, clamped to `0–1` | `0.28` |
| `IconGrid.alignmentHighlight` | Enables the slightly stronger guide shown near the active drawing point or a node being moved. It does not enable snapping. | Boolean or `on/off`, `yes/no`, `true/false`, `1/0` | `true` |
| `IconGrid.alignmentTolerance` | Maximum on-screen distance from the active point to a guide before the guide highlights. Smaller values are more precise. | Number `1–20` in screen points | `2` |

## Advanced count-based and canvas controls

You normally do not need these parameters. They remain available for backward compatibility and for layouts that cannot be described by one `gridSize`.

| Parameter | What it controls | Accepted value | Default |
| --- | --- | --- | --- |
| `IconGrid.columns` | Number of equal cell divisions across the canvas width **when `gridSize` is unset**. More columns make narrower cells: cell width is `width / columns`. | Integer `1–256` | `24` |
| `IconGrid.rows` | Number of equal cell divisions across the canvas height **when `gridSize` is unset**. More rows make shorter cells: cell height is `height / rows`. | Integer `1–256` | `24` |
| `IconGrid.rings` | Number of evenly distributed circular guides **when `gridSize` is unset**. With `gridSize`, up to two complete inner circles are instead spaced by that exact unit. | Integer `0–128` | `2` |
| `IconGrid.width` | Width of the fixed construction canvas in font units. It is not the glyph advance width. | Positive number | Font UPM, then active-master cap height, then `1000` |
| `IconGrid.height` | Height of the fixed construction canvas in font units. | Positive number | Font UPM, then active-master cap height, then `1000` |
| `IconGrid.origin` | How the fixed canvas is anchored horizontally to the glyph advance and vertically before the baseline offset is applied. | One of the nine origin names below | `bottom-center` |
| `IconGrid.baselineOffset` | Explicit vertical translation of the canvas; positive values move it down. Setting it replaces automatic Mid Height or cap-height centering. | Finite number in font units | `height / 2 − midHeight` when usable; otherwise `(height − capHeight) / 2` for the default origin, then `0` |

Supported origins are:

- `bottom-left`, `bottom-center`, `bottom-right`
- `center-left`, `center`, `center-right`
- `top-left`, `top-center`, `top-right`

The horizontal part aligns the canvas to the active layer’s advance: `left` puts its left edge at x=0, `center` puts its center at half the advance, and `right` puts its right edge at the advance. The grid is never stretched to match the glyph advance.

Without `gridSize`, square cells require:

```text
IconGrid.width / IconGrid.columns = IconGrid.height / IconGrid.rows
```

Leaving all four values unset provides the normal square result automatically.

## Scope and inheritance

Each setting resolves independently:

1. a valid, active value on the current master;
2. a valid, active value at font scope;
3. for `gridSize`, the active master’s preferred H stem;
4. the built-in default.

For a weight-specific construction unit, prefer the master’s native stem metric. Put an explicit `gridSize` on the master only when the icon construction unit intentionally differs. Shared appearance settings such as `color` can be placed at font scope.

Native Mid Height is separate from custom-parameter inheritance. The reporter
reads the active master's value from the font's first usable, unfiltered Mid
Height definition. Filtered values and overshoot do not affect placement.

Disabled parameters are ignored. Invalid values fall through safely and produce one deduplicated `IconGrid:` warning in the Macro Panel per plug-in session. Duplicate active records are ambiguous: the reporter warns and uses the last value, while the Glyphs MCP parameter tool refuses to modify that name until the duplicate is resolved.

## Behavior that needs no parameter

- The default canvas is one em square and centered horizontally on the glyph advance.
- Its vertical center uses the active master's Mid Height when usable, then the
  baseline/cap-height midpoint.
- Its live circle is `capHeight / 0.8` when padding is unstored. The landscape
  keyline spans baseline to cap height only when their midpoint is also the
  construction center.
- The square background grid extends by at least four cells on every side, capped at eight.
- Stem-sized construction draws at most two inner circles; the circular keyline makes two or three visible circles in typical masters.
- Draw, Rectangle/Square, and Circle show alignment feedback near guides.
- Edit highlights only while selected nodes actually move.
- Pencil highlights only during an active stroke; Annotation never does.

See the [user guide](USER_GUIDE.md) for setup steps, examples, and troubleshooting.
