# Behavioral specification

## Scope

`GlyphsIconGridReporter` is a `ReporterPlugin` with one command: **View → Show Icon Grid**. It draws behind the active glyph and provides no dialog, context menu, palette, shortcut, or dependency on Vanilla. Drawing is suppressed for text, hand, and zoom tools.

The reporter is observational. It does not mutate glyphs, paths, components, selections, guides, snapping preferences, custom parameters, exports, or files.

## Layering

1. `glyphs_icon_grid.config` converts plain parameter records into a validated `GridConfig`.
2. `glyphs_icon_grid.geometry` converts a width and `GridConfig` into bounded numeric primitives.
3. `plugin.py` extracts plain data from Glyphs objects, batches primitives into `NSBezierPath` instances, and strokes them behind the glyph.

The first two layers import neither Glyphs nor AppKit. There are no mutable global geometry caches.

## Geometry

The canvas has configured fixed width and height. By default, both equal the font UPM and both axes have 24 divisions, producing a one-em square construction canvas of square cells. Its horizontal origin anchors the left edge at x=0, the center at half the active layer advance, or the right edge at the advance. With the default `bottom-center` origin, the automatic baseline offset is `(height − xHeight) / 2`, placing the canvas center halfway between the baseline and x-height. The layer width therefore controls horizontal placement only: it never changes cell spacing, rings, or keyline proportions. An explicit `baselineOffset` replaces the automatic vertical placement.

Without a grid-size override, the grid uses `IconGrid.width / columns` and `IconGrid.height / rows` spacing. These values are equal under automatic defaults. A valid `IconGrid.gridSize` replaces both with one square-cell size in font units and takes precedence over the division counts. The background grid extends symmetrically by equal whole-cell counts on all sides. It targets at least one complete cell beyond the active master’s cap-height/ascender and descender extents, capped at six cells per side. The background therefore stays square and compact under default geometry while allowing exceptional artwork outside the glyph square; the canvas and live-area frames remain unchanged.

Grid phase and major-line cadence are centered on the translated canvas in both axes. In the default `odd` mode, grid lines lie at half-cell offsets from the center, placing one complete cell across the horizontal and vertical construction axes. No axis grid line exists in this mode. In `even` mode, grid lines lie at whole-cell offsets, with one vertical and one horizontal axis line intersecting at the canvas center. Every `majorEvery`th border away from the center is major, symmetrically on both sides.

The live-area inset is `padding` effective horizontal cells and `padding` effective vertical cells. Without `IconGrid.gridSize`, the configured ring count is distributed evenly through the live radius. With `gridSize`, rings use that same value as their exact radial spacing, up to the largest complete multiple inside the live area; the ring count is ignored. Spokes share the ring center and are evenly spaced over 360°.

The ring, spoke, and keyline center is the canvas center. Under default placement, its x coordinate is half the glyph advance and its y coordinate is half the active master’s x-height. This is the font-aligned construction center for inline icon design; the reporter does not reposition glyph outlines.

Keylines scale Material’s 24-unit proportions to the live-circle diameter:

- circle: 20/20 of the live diameter
- square: 18/20 × 18/20
- portrait: 16/20 × 20/20
- landscape: 20/20 × 16/20

Stroke widths are specified in screen pixels and divided by the current zoom scale.

## Alignment highlighting

The reporter reads the current `toolEventDelegate` and unwraps its selected `GSToolGroup.currentTool` when present. It uses the documented native `dragging` and `dragStart` state plus selected `GSNode` objects during Glyphs' normal background redraw. It retains selected node objects and their positions from the last non-drag draw. A Select/Edit drag becomes eligible only after a selected node's coordinates actually change; newly selected nodes also become eligible during a Draw-tool click-drag.

For Draw, Rectangle/Square, and Circle only, a scoped `MOUSEMOVED` callback converts the event through the Edit view's cross-version `getActiveLocation_` API and requests the redraw Glyphs requires for hover feedback. The cached point is accepted only for the active layer and only while one of those exact tools remains selected. Rectangle and Circle previews do not add nodes until mouse-up, so their native in-progress preview endpoint takes precedence during a drag. A stale pre-drag hover is never reused when an active endpoint cannot be read.

Pencil contributes the last point only after its native stroke point array contains actual movement. `AnnotationTool` is explicitly excluded before any construction-point lookup. Select/Edit keeps its movement-only behavior, so passive Edit movement, lasso selection, static selections, and unrelated drags remain excluded. Tool-group numbers are not used because their values and meanings differ between Glyphs 3 and Glyphs 4.

Eligible node positions are hit-tested by the pure geometry core against minor, major, and axis lines; canvas and live-area frames; rings; spokes; and enabled keylines. Point-to-segment, circle-perimeter, and rectangle-perimeter distances are finite and bounded, and exact coincident primitives are reported once.

`IconGrid.alignmentTolerance` defaults to two screen points and is divided by the live Edit-view scale before hit-testing. Every guide inside the tolerance highlights, so both grid lines react at an intersection. The highlight is drawn last in the background pass using the configured color, a 1.4-screen-pixel stroke, and `min(1, opacity × 1.6)` alpha. This makes an aligned guide only a little more visible while glyph outlines remain above it. Text, hand, and zoom tools suppress the reporter.

## Safety behavior

The reporter is a no-op without a usable layer, glyph, font, active master, finite positive layer width, finite positive configured width and height, or supported drawing context. Alignment highlighting additionally requires either a node that actually participates in a native drag or an active outline-construction point from a supported tool. Spacing values that would exceed the 256-cell or 128-ring geometry limits are invalid. Values outside documented limits, malformed colors, non-finite numbers, and unknown origins fall through the master/font/default chain. Warnings are deduplicated by complete message for the reporter session.

Glyphs 3 and Glyphs 4 are handled through their shared duck-typed layer/font/master/custom-parameter APIs. The adapter tests inject both shapes and assert identical core geometry.
