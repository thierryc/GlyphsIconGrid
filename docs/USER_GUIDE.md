# GlyphsIconGrid user guide

GlyphsIconGrid draws an icon-construction grid behind the active glyph in Glyphs. It is a visual reporter: it does not change outlines, add snapping, affect exports, or save the document by itself.

## Install

GlyphsIconGrid supports Glyphs 3.5 and Glyphs 4.

1. Download and unzip a release.
2. Double-click `IconGrid.glyphsReporter`, or move it into the `Plugins` folder for the Glyphs version you use.
3. Restart Glyphs.
4. Open a glyph in Edit view.

For a source checkout, the plug-in bundle is `IconGrid.glyphsReporter` at the repository root. Restart Glyphs after replacing or relinking a development copy.

## Show or hide the grid

Choose **View → Show Icon Grid**. Choose it again to hide the reporter.

The grid is drawn only in Edit view. GlyphsIconGrid deliberately hides the whole reporter while the Text, Hand, or Zoom tool is handling events, then restores it when you return to an outline-editing or outline-creation tool.

## Default construction geometry

With no `IconGrid.*` custom parameters, the plug-in provides an icon-oriented layout:

- a 24 × 24 construction canvas;
- equal width and height, using the font UPM, then the active master's cap height, then `1000` as safe fallbacks;
- square cells because the default dimensions and divisions are equal;
- an `odd`, cell-centered grid phase: one central cell is bisected by both construction axes;
- horizontal centering on the active layer's advance width;
- vertical centering halfway between the baseline and x-height;
- two cells of inset padding around the live area;
- a major line every four cells, eight radial spokes, automatic concentric rings, and Material-derived keylines;
- a blue `#0A84FF` color at `0.28` opacity, distinct from Glyphs' metric and user guides.

The background grid extends by whole cells beyond the construction canvas in all four directions. It includes at least one extra cell and expands far enough to leave working room past the ascender/cap-height and descender when possible. Automatic overflow is capped at six cells per side so the grid remains local to the glyph.

The canvas itself, live-area frames, circles, spokes, and keylines stay inside their configured bounds. Only the background grid overflows; its cells remain square under the default configuration.

## Configure a font or master

Add parameters in **File → Font Info → Font → Custom Parameters**. A font-level value applies to every master that does not override it. Add the same parameter to a master to override that single value for that master.

Resolution happens independently for every field:

1. a valid, active parameter on the current master;
2. a valid, active font parameter;
3. the built-in default.

Disabled parameters are ignored. Invalid values fall through safely and produce one deduplicated warning in the Macro Panel per plug-in session. Unrelated custom parameters are untouched.

The available settings are:

- geometry: `IconGrid.gridSize`, `IconGrid.gridMode`, `IconGrid.columns`, `IconGrid.rows`, `IconGrid.width`, `IconGrid.height`, `IconGrid.origin`, and `IconGrid.baselineOffset`;
- construction guides: `IconGrid.padding`, `IconGrid.majorEvery`, `IconGrid.rings`, `IconGrid.spokes`, and `IconGrid.showKeylines`;
- appearance: `IconGrid.color` and `IconGrid.opacity`;
- alignment cue: `IconGrid.alignmentHighlight` and `IconGrid.alignmentTolerance`.

See [Custom parameter reference](PARAMETERS.md) for accepted types, ranges, defaults, and every supported origin.

### Position and cell shape

The default `bottom-center` origin centers the canvas horizontally on the glyph advance. Its automatic baseline offset places the canvas center at half the x-height. Setting `IconGrid.baselineOffset` explicitly replaces that automatic vertical placement; positive values move the canvas down.

For square cells, keep this relationship:

```text
IconGrid.width / IconGrid.columns = IconGrid.height / IconGrid.rows
```

Leaving width, height, columns, and rows unset gives the standard square result. Explicit values are honored, so unequal ratios intentionally create rectangular cells.

Set `IconGrid.gridSize` to the master’s construction unit in font units. This one value controls both square-cell size and the radial gap between circles. It takes precedence over columns, rows, and ring count. Padding remains measured in effective grid cells.

### Grid centering mode

The default `IconGrid.gridMode = odd` places one complete grid cell at the canvas center. The horizontal and vertical construction axes bisect that cell, so no grid line lies on either axis. This is the usual icon-layout arrangement.

Set `IconGrid.gridMode = even` when a grid border must coincide with each construction axis. The mode can be shared at font scope or overridden on an individual master.

## Alignment highlighting by tool

When `IconGrid.alignmentHighlight` is enabled, a construction guide becomes slightly wider and more opaque when the relevant point is within `IconGrid.alignmentTolerance`. The default tolerance is a strict two screen points and remains visually constant as the zoom changes. At a crossing, every matching guide highlights together.

| Tool | When the cue is active |
| --- | --- |
| Draw | Whenever the pointer is near a guide; while constructing, the native active endpoint is used. |
| Rectangle/Square | Whenever the pointer is near a guide; during a drag, the native shape-preview endpoint is used. |
| Circle | Whenever the pointer is near a guide; during a drag, the native shape-preview endpoint is used. |
| Edit | Only during a native drag after one or more selected nodes actually move. A passive pointer, static selection, or lasso does not activate it. |
| Pencil | Only during an active freehand stroke after movement has produced stroke points. |
| Annotation | Never. Annotation drawing is intentionally excluded. |
| Text, Hand, Zoom | The reporter is suppressed while these tools handle events. |

The cue is informational only. It does not snap or move points, and its temporary state is never written to the font.

## Useful recipes

### Match each master’s icon weight

Leave shared settings unstored when the built-in defaults are suitable. Put only the weight-dependent construction unit on each master. For a 1000-UPM icon family, start with:

```text
Regular master:
IconGrid.gridSize = 34

Bold master:
IconGrid.gridSize = 72
```

This produces exact 34-unit Regular cells and circle gaps, and exact 72-unit Bold cells and gaps. Scale the value proportionally for another UPM, or use the actual construction/stroke unit of each master.

### Use advanced count-based settings

Normally, `IconGrid.gridSize` is enough. Leave it unset only when you intentionally want separate `columns`, `rows`, and `rings` counts. See the [custom parameter reference](PARAMETERS.md) for those advanced controls.

### Design beyond the usual icon bounds

No parameter is required. The background grid already overflows the construction canvas on every side. Use that area for deliberate overshoots while keeping the core keylines centered on the icon canvas.

### Use a custom canvas

Set `IconGrid.width` and `IconGrid.height` in font units, then choose matching column and row counts for the desired cell size. Use an origin such as `bottom-left`, `center`, or `top-right` to choose how that fixed canvas is anchored to the active layer's advance.

### Return to automatic behavior

Delete the relevant `IconGrid.*` record from the master to inherit the font value. Delete it from both master and font scopes to use the built-in default. Through Glyphs MCP, deletion is represented by JSON `null`; see [Configuring GlyphsIconGrid with Glyphs MCP](GLYPHS_MCP.md).

## Troubleshooting

### The grid is not visible

- Confirm **View → Show Icon Grid** is enabled.
- Open a glyph in Edit view with a valid, positive layer width.
- Switch away from Text, Hand, or Zoom; those tools intentionally suppress the reporter.
- Confirm `IconGrid.opacity` is not set to `0` and the chosen color has enough contrast.
- Restart Glyphs after installing or replacing the plug-in.

### The grid is not centered as expected

- Remove explicit `IconGrid.origin`, `IconGrid.baselineOffset`, `IconGrid.width`, and `IconGrid.height` values to restore the default font-aligned placement.
- Check the active master's x-height. The automatic vertical center is halfway between its baseline and x-height.
- Check for a master-level override; it takes precedence over the font one.
- Check `IconGrid.gridMode`: `odd` centers a cell on the construction axes, while `even` centers intersecting grid lines.
- Confirm the glyph has the intended advance width. Horizontal centering follows the active layer's advance, not its outline bounds.

### The cells are rectangular

Compare width per column with height per row. Equal column and row counts alone do not guarantee square cells when width and height differ. Remove the four size/division overrides for the default square grid, or set values that satisfy the ratio shown above.

If `IconGrid.gridSize` is present, it intentionally overrides the grid and circle count settings with one exact construction unit. Check the active master as well as font scope before changing the count settings.

### A guide does not highlight

- Confirm `IconGrid.alignmentHighlight` is true.
- With Edit, move a selected node; merely moving the pointer or selecting a node is intentionally inactive.
- With Pencil, begin an actual stroke. With Annotation, no alignment cue is available.
- Move closer to the guide or increase `IconGrid.alignmentTolerance` slightly. The default of two screen points is deliberately precise; accepted values are `1–20`.
- Check whether the active master disables or overrides the font parameter.

### A parameter appears to be ignored

Open the Macro Panel and look for an `IconGrid:` warning. Values outside the documented range and unsupported origin names fall through to the next scope or default. Disabled records are ignored. Duplicate active records are ambiguous: the reporter warns and uses the last one, while Glyphs MCP refuses to mutate that parameter until the duplicate is resolved. Compare both font and active-master scopes before changing anything.
