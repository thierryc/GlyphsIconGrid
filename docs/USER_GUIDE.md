# GlyphsIconGrid user guide

GlyphsIconGrid draws an icon-construction grid behind the active glyph in Glyphs. It is a visual reporter: it does not change outlines, add snapping, affect exports, or save the document by itself.

## Install

GlyphsIconGrid supports Glyphs 3.5 and Glyphs 4.

1. Download and unzip a release.
2. Double-click `IconGrid.glyphsReporter`, or move it into the `Plugins` folder for the Glyphs version you use.
3. Restart Glyphs.
4. Open a glyph in Edit view.

For a source checkout, the plug-in bundle is `IconGrid.glyphsReporter` at the repository root. Restart Glyphs after replacing or relinking a development copy.

### Install the optional AI skill

The release ZIP also includes `Install GlyphsIconGrid Skill.command`. Double-click it and choose:

1. **Codex, Gemini, and Cursor** for the shared `~/.agents/skills` location;
2. **Claude** for `~/.claude/skills`;
3. **All supported clients** for both locations.

No repository checkout or Python installation is required. When updating an existing skill, the installer asks before replacement and keeps the previous folder as a dated backup. Restart the AI client after installation.

The skill does not install or configure the Glyphs MCP server. Follow the [Glyphs MCP guide](GLYPHS_MCP.md) for the local server connection and guarded editing workflow.

## Show or hide the grid

Choose **View → Show Icon Grid**. Choose it again to hide the reporter.

The grid is drawn only in Edit view. GlyphsIconGrid deliberately hides the whole reporter while the Text, Hand, or Zoom tool is handling events, then restores it when you return to an outline-editing or outline-creation tool.

## Default construction geometry

With no `IconGrid.*` custom parameters, the plug-in provides an icon-oriented layout:

- a 24 × 24 construction canvas;
- equal width and height, using the font UPM, then the active master's cap height, then `1000` as safe fallbacks;
- square cells and circular spacing equal to the active master’s capital-H stem when one is defined;
- the 24 × 24 count-based spacing when no usable stem is available;
- an `odd`, cell-centered grid phase: one central cell is bisected by both construction axes;
- horizontal centering on the active layer's advance width;
- vertical centering halfway between the baseline and cap height;
- a metric-fitted live circle whose landscape keyline spans baseline to cap height;
- a major line every four cells, eight radial spokes, up to two inner concentric circles, and Material-derived keylines;
- a blue `#0A84FF` color at `0.28` opacity, distinct from Glyphs' metric and user guides.

The background grid extends by whole cells beyond the construction canvas in all four directions. It includes at least four extra cells per side and expands far enough to leave working room past the ascender/cap-height and descender when possible. Automatic overflow is capped at eight cells per side so the field covers more of the Edit view without becoming unbounded.

The canvas itself, live-area frames, circles, spokes, and keylines stay inside their configured bounds. Only the background grid overflows; its cells remain square under the default configuration. With no stored padding, the live diameter is `(cap height − baseline) / 0.8`, clamped to the canvas. A 700-unit cap height therefore produces an 875-unit live circle. Stem-sized construction uses at most two inner circles. Together with the outer circular keyline, this produces no more than three useful visible circles.

## Configure a font or master

Add parameters in **File → Font Info → Font → Custom Parameters**. A font-level value applies to every master that does not override it. Add the same parameter to a master to override that single value for that master.

Resolution happens independently for every field:

1. a valid, active parameter on the current master;
2. a valid, active font parameter;
3. the built-in default.

Disabled parameters are ignored. Invalid values fall through safely and produce one deduplicated warning in the Macro Panel per plug-in session. Unrelated custom parameters are untouched.

For normal use, define weight-specific stems in **File → Font Info → Masters → Stems** and leave `IconGrid.gridSize` unset. The reporter prefers a named H horizontal stem, then a named H vertical stem. `IconGrid.gridMode` is the only setup control most users may need:

- the master stem sets both square-cell size and circular-guide spacing;
- an explicit `gridSize` overrides that automatic value;
- `gridMode = odd` centers a cell on the axes and is the default;
- `gridMode = even` puts grid lines on the axes.

Everything else is optional:

- guide options: padding, major-line cadence, spokes, keylines, and the legacy count-based ring controls;
- appearance options: color and opacity;
- alignment options: highlight on/off and screen-point tolerance;
- advanced layout options: canvas width, height, division counts, origin, and baseline offset.

See the [plain-language parameter guide](PARAMETERS.md) for what every setting changes, when it is used, accepted values, and defaults.

### Position and cell shape

The default `bottom-center` origin centers the canvas horizontally on the glyph advance. Its automatic baseline offset places the canvas center halfway between the baseline and cap height. Setting `IconGrid.baselineOffset` explicitly replaces that automatic vertical placement; positive values move the canvas down.

The automatic live diameter is `cap height / 0.8`. Material’s landscape rectangle is 80% of that diameter, so it runs exactly from the baseline to cap height. The 90% square is intentionally larger than that vertical span. For the default metrics, the resulting keylines are an 875-unit circle, a 787.5-unit square, a 700 × 875 portrait rectangle, and an 875 × 700 landscape rectangle.

For square cells, keep this relationship:

```text
IconGrid.width / IconGrid.columns = IconGrid.height / IconGrid.rows
```

Leaving width, height, columns, and rows unset gives the standard square result. Explicit values are honored, so unequal ratios intentionally create rectangular cells.

Set `IconGrid.gridSize` only when the desired construction unit differs from the master’s H stem. This one value controls both square-cell size and the radial gap between circles. It takes precedence over columns, rows, and ring count. Store `IconGrid.padding` only when an intentional cell-based inset should replace the automatic metric-fitted live area.

The baseline-to-cap-height relationship is `x = (capHeight − baseline) / gridSize`. The plug-in keeps the H stem exact even when `x` is fractional.

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

For responsiveness, the Edit-tool cue is temporarily suppressed when more than 64 distinct selected-node positions move together. The nodes still move normally; only the informational highlight is omitted for that large drag.

## Useful recipes

### Match each master’s icon weight

Leave `IconGrid.*` settings unstored and define a stem for every master. For a new 1000-UPM icon family, the generic report starts Regular and Bold at:

```text
Regular H stem = 84
Bold H stem    = 135
```

This produces exact 84-unit Regular cells and circle gaps, and exact 135-unit Bold cells and gaps. Scale the scaffold proportionally for another UPM, or use the actual measured construction/stroke unit of each master.

### Use advanced count-based settings

Normally, `IconGrid.gridSize` is enough. Leave it unset only when you intentionally want separate `columns`, `rows`, and `rings` counts. See the [custom parameter reference](PARAMETERS.md) for those advanced controls.

### Design beyond the usual icon bounds

No parameter is required. The background grid already extends by at least four cells beyond the construction canvas on every side. Use that area for deliberate overshoots while keeping the core keylines centered on the icon canvas.

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
- Check the active master's cap height. The automatic vertical center is halfway between its baseline and cap height.
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
- For Edit drags, reduce selections larger than 64 distinct node positions if the temporary cue is needed.
- Move closer to the guide or increase `IconGrid.alignmentTolerance` slightly. The default of two screen points is deliberately precise; accepted values are `1–20`.
- Check whether the active master disables or overrides the font parameter.

### A parameter appears to be ignored

Open the Macro Panel and look for an `IconGrid:` warning. Values outside the documented range and unsupported origin names fall through to the next scope or default. Disabled records are ignored. Duplicate active records are ambiguous: the reporter warns and uses the last one, while Glyphs MCP refuses to mutate that parameter until the duplicate is resolved. Compare both font and active-master scopes before changing anything.
