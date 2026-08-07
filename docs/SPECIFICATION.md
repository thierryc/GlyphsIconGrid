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

The canvas has configured fixed width and height. By default, both equal the
font UPM and both axes have 24 divisions, producing a one-em square
construction canvas of square cells. Its horizontal origin anchors the left
edge at x=0, the center at half the active layer advance, or the right edge at
the advance. With the default `bottom-center` origin, the reporter reads the
first usable unfiltered `GSMetricsTypeMidHeight` definition from `font.metrics`
and the matching active-master position from `master.metrics`, with
`metricValues` as a compatibility fallback. It ignores metric overshoot. A
usable position produces `baselineOffset = height / 2 − midHeight`; otherwise
the existing `(height − capHeight) / 2` fallback applies, then zero when neither
metric is usable. The layer width therefore controls horizontal placement only:
it never changes cell spacing, rings, or keyline proportions. An explicit
`baselineOffset` replaces the automatic vertical placement, and non-default
origins retain their configured anchor behavior.

Without a grid-size custom parameter, the reporter first reads the active master’s stem metrics. It prefers a named capital-H horizontal stem, then a named H vertical stem, then the first horizontal and vertical definitions. A usable value becomes the exact square-cell size and circular spacing. If no usable stem exists, the grid uses `IconGrid.width / columns` and `IconGrid.height / rows` spacing. A valid `IconGrid.columns`, `IconGrid.rows`, or `IconGrid.rings` parameter intentionally selects that count-based model. An explicit valid `IconGrid.gridSize` replaces either automatic path and takes precedence over the division counts. The background grid extends symmetrically by equal whole-cell counts on all sides. It includes at least four complete cells beyond the construction canvas and expands far enough to clear the active master’s cap-height/ascender and descender extents, capped at eight cells per side. The expanded field remains finite while covering more of the glyph drawing area; the canvas and live-area frames remain unchanged.

Grid phase and major-line cadence are centered on the translated canvas in both axes. In the default `odd` mode, grid lines lie at half-cell offsets from the center, placing one complete cell across the horizontal and vertical construction axes. No axis grid line exists in this mode. In `even` mode, grid lines lie at whole-cell offsets, with one vertical and one horizontal axis line intersecting at the canvas center. Every `majorEvery`th border away from the center is major, symmetrically on both sides.

When `IconGrid.padding` is unstored and cap height is valid, the live area is a centered square whose diameter is `(capHeight − baseline) / 0.8`, clamped to the smaller canvas dimension. With the default metrics this is 875 units. A valid stored padding value replaces that automatic fit and insets the live area by `padding` effective horizontal and vertical cells. If cap height is unavailable, the fallback is two cells. Without `IconGrid.gridSize`, the configured ring count is distributed evenly through the live radius and defaults to two. With `gridSize`, up to two inner rings use that same value as their exact radial spacing; the ring count is ignored. The enabled circular keyline supplies the outer construction circle, so the reporter never shows more than three concentric construction circles. Spokes share the ring center and are evenly spaced over 360°.

The ring, spoke, and keyline center is the canvas center. Under default
placement, its x coordinate is half the glyph advance and its y coordinate is
the active master's usable Mid Height position, falling back to halfway between
baseline and cap height. This is the font-aligned construction center for
inline icon design; the reporter does not reposition glyph outlines.

Keylines scale Material’s 24-unit proportions to the live-circle diameter:

- circle: 20/20 of the live diameter
- square: 18/20 × 18/20
- portrait: 16/20 × 20/20
- landscape: 20/20 × 16/20

Consequently, under automatic sizing the landscape keyline spans exactly from
baseline to cap height only when the construction center is their midpoint. A
distinct Mid Height translates the keyline without changing its cap-height-
derived dimensions. The 18/20 square is a distinct, larger vertical
construction shape.

Stroke widths are specified in screen pixels and divided by the current zoom scale.

## Alignment highlighting

The reporter reads the current `toolEventDelegate` and unwraps its selected `GSToolGroup.currentTool` when present. It uses the documented native `dragging` and `dragStart` state plus selected `GSNode` objects during Glyphs' normal background redraw. It retains selected node objects and their positions from the last non-drag draw. A Select/Edit drag becomes eligible only after a selected node's coordinates actually change; newly selected nodes also become eligible during a Draw-tool click-drag.

For Draw, Rectangle/Square, and Circle only, a scoped `MOUSEMOVED` callback converts the event through the Edit view's cross-version `getActiveLocation_` API. It hit-tests only the configuration, geometry, guide catalog, and positive scale cached by the latest background render. A visible guide change invalidates only the active `graphicView`, allowing AppKit to coalesce display work; the callback never requests an application-wide redraw. The cached point is accepted only for the active layer and only while one of those exact tools remains selected. Rectangle and Circle previews do not add nodes until mouse-up, so their native in-progress preview endpoint takes precedence during a drag. Callback invalidation is suppressed throughout a native drag, and a stale pre-drag hover is never reused when an active endpoint cannot be read.

Pencil contributes the last point only after its native stroke point array contains actual movement. `AnnotationTool` is explicitly excluded before any construction-point lookup. Select/Edit keeps its movement-only behavior, so passive Edit movement, lasso selection, static selections, and unrelated drags remain excluded. Tool-group numbers are not used because their values and meanings differ between Glyphs 3 and Glyphs 4.

Eligible node positions are hit-tested in one batch by the pure geometry core against minor, major, and axis lines; canvas and live-area frames; rings; spokes; and enabled keylines. Point-to-segment, circle-perimeter, and rectangle-perimeter distances are finite and bounded, and exact coincident primitives are reported once. To keep native editing responsive, the temporary cue is suppressed when more than 64 distinct selected-node positions move together.

`IconGrid.alignmentTolerance` defaults to two screen points and is divided by the live Edit-view scale before hit-testing. Every guide inside the tolerance highlights, so both grid lines react at an intersection. The highlight is drawn last in the background pass using the configured color, a 1.4-screen-pixel stroke, and `min(1, opacity × 1.6)` alpha. This makes an aligned guide only a little more visible while glyph outlines remain above it. Text, hand, and zoom tools suppress the reporter.

## Safety behavior

The reporter is a no-op without a usable layer, glyph, font, active master, finite positive layer width, finite positive configured width and height, supported drawing context, or finite positive cached Edit-view scale. Alignment highlighting additionally requires either a node that actually participates in a native drag or an active outline-construction point from a supported tool. Mouse-observer failures are contained, clear temporary hover state, and warn once by exception type. Spacing values that would exceed the 256-cell or 128-ring geometry limits are invalid. Values outside documented limits, malformed colors, non-finite numbers, and unknown origins fall through the master/font/default chain. Warnings are deduplicated by complete message for the reporter session.

Glyphs 3 and Glyphs 4 are handled through their shared duck-typed
layer/font/master/metric/stem/custom-parameter APIs. Metric and stem values are
read only; the reporter never creates or changes their definitions. The adapter
tests inject both shapes and assert identical core geometry.
