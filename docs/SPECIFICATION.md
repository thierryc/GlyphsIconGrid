# Behavioral specification

## Scope

`GlyphsIconGrid` is a `ReporterPlugin` with one command: **View → Show Icon Grid**. It draws behind the active glyph and provides no dialog, context menu, palette, shortcut, or dependency on Vanilla. Drawing is suppressed for text and hand tools.

The reporter is observational. It does not mutate glyphs, paths, components, selections, guides, snapping preferences, custom parameters, exports, or files.

## Layering

1. `icon_grid.config` converts plain parameter records into a validated `GridConfig`.
2. `icon_grid.geometry` converts a width and `GridConfig` into bounded numeric primitives.
3. `plugin.py` extracts plain data from Glyphs objects, batches primitives into `NSBezierPath` instances, and strokes them behind the glyph.

The first two layers import neither Glyphs nor AppKit. There are no mutable global geometry caches.

## Geometry

The canvas has configured fixed width and height. Width defaults to 1.5 times the font UPM, covering 1500 units in a 1000-UPM font. Its horizontal origin anchors the left edge at x=0, the center at half the active layer advance, or the right edge at the advance. Its vertical origin anchors the bottom, center, or top at y=0. The layer width therefore controls placement only: it never changes cell spacing, rings, or keyline proportions. A positive `baselineOffset` translates the complete canvas downward by that many font units, allowing part of the grid to sit below the font baseline.

The rectangular grid uses `IconGrid.width / columns` and `IconGrid.height / rows` spacing. Cadence starts from the selected horizontal anchor and y=0. Glyph y=0 remains an axis line whenever it intersects the translated canvas; every `majorEvery`th line away from an anchor is major.

The live-area inset is `padding` horizontal cells and `padding` vertical cells. Rings are concentric true circles with equal radial spacing up to the largest circle contained by the live area. Spokes share the ring center and are evenly spaced over 360°.

Keylines scale Material’s 24-unit proportions to the live-circle diameter:

- circle: 20/20 of the live diameter
- square: 18/20 × 18/20
- portrait: 16/20 × 20/20
- landscape: 20/20 × 16/20

Stroke widths are specified in screen pixels and divided by the current zoom scale.

## Hover highlighting

While the reporter is active, it observes Glyphs' mouse-moved notification and converts the current event to coordinates in the active layer. Hit-testing is performed by the pure geometry core against minor, major, and axis lines; canvas and live-area frames; rings; spokes; and enabled keylines. Point-to-segment, circle-perimeter, and rectangle-perimeter distances are finite and bounded, and exact coincident primitives are reported once.

`IconGrid.hoverTolerance` is measured in screen points and divided by the live Edit-view scale before hit-testing. Every guide inside the tolerance highlights, so both grid lines react at an intersection. The highlight is drawn last in the background pass using the configured color, a two-screen-point stroke, and `min(1, opacity × 2.5)` alpha. Glyph outlines therefore remain above it.

The callback is registered once when the reporter activates and removed when it deactivates. A redraw is requested only when the hovered guide set changes. Moving to another window, using the text or hand tool, losing a valid active layer, or deactivating the reporter clears the ephemeral hover state.

## Safety behavior

The reporter is a no-op without a usable layer, glyph, font, active master, finite positive layer width, finite positive configured width and height, current mouse event, or supported drawing context. Values outside documented limits, malformed colors, non-finite numbers, and unknown origins fall through the master/font/default chain. Warnings are deduplicated by complete message for the reporter session.

Glyphs 3 and Glyphs 4 are handled through their shared duck-typed layer/font/master/custom-parameter APIs. The adapter tests inject both shapes and assert identical core geometry.
