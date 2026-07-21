# GlyphsIconGrid

GlyphsIconGrid is a no-dialog reporter plug-in for drawing an icon construction grid behind the active glyph in Glyphs 3 and Glyphs 4. It provides an origin-aware rectangular grid, a padded live area, concentric circular guides, radial spokes, and Material-derived circle/square/portrait/landscape keylines. The plug-in never changes outlines, snapping, export behavior, or the saved document on its own.

Toggle it with **View → Show Icon Grid**. Every setting is a font custom parameter, optionally overridden on the active master, so settings travel with the `.glyphs` file and can be edited through automation such as [Glyphs MCP](https://github.com/thierryc/Glyphs-mcp).

## Install

1. Download and unzip a release.
2. Double-click `IconGrid.glyphsReporter`, or move it to the plug-in folder for the Glyphs version you use.
3. Restart Glyphs.
4. Open an Edit view and choose **View → Show Icon Grid**.

The source bundle targets Glyphs 3.5 build 3530 and Glyphs 4.0 build 3875. Version `0.1.0` will not be published until the live-test checklist passes in both builds.

## Configure

Add parameters in **File → Font Info → Font → Custom Parameters**. Add a parameter with the same name to a master to override only that value for the active master. For example:

```text
IconGrid.columns = 24
IconGrid.rows = 24
IconGrid.origin = center
IconGrid.padding = 2
IconGrid.baselineOffset = 100
IconGrid.rings = 10
IconGrid.spokes = 8
```

See [the complete parameter reference](docs/PARAMETERS.md) and [behavioral specification](docs/SPECIFICATION.md). Parameter changes redraw immediately when Glyphs refreshes the Edit view; the generic `set_custom_parameters` Glyphs MCP tool also requests a redraw and never saves implicitly.

## Design rationale

The grid follows three established icon-design ideas while remaining format-neutral:

- Apple recommends starting from its platform templates and visually centering artwork rather than treating geometric centering as absolute. IconGrid therefore supplies guides, not constraints or snapping. See [Apple’s app-icon guidance](https://developer.apple.com/design/human-interface-guidelines/app-icons) and [Apple Design Resources](https://developer.apple.com/design/resources/).
- Google’s Material 24-unit keyline uses a 20-unit circle, 18-unit square, 16×20 portrait rectangle, and 20×16 landscape rectangle. IconGrid scales those proportions to the configured live circle. See [Material system icon keylines](https://m2.material.io/design/iconography/system-icons.html#grid-and-keyline-shapes).
- IBM Carbon recommends a consistent base grid and optical adjustments for visual balance. IconGrid deliberately leaves those optical decisions to the designer. See [Carbon icon design](https://carbondesignsystem.com/guidelines/icons/design/).

Circular guides are always true circles, centered on the transformed canvas even when the glyph width and configured height differ.
Set `IconGrid.baselineOffset` to a positive font-unit value when the construction canvas should extend below the font baseline; y=0 remains a highlighted grid axis.

## Develop and test

The core imports neither Glyphs nor AppKit:

```sh
python3 -m unittest discover -v
python3 -m compileall -q IconGrid.glyphsReporter tests scripts
python3 scripts/validate.py IconGrid.glyphsReporter --target both
```

The deterministic tests assert numeric geometry rather than screenshots. The test fixture at `tests/fixtures/IconGrid-Test.glyphs` is disposable and contains two masters with different widths and overrides.

## License and attribution

Apache-2.0. The official GlyphsSDK reporter template and universal wrapper are attributed in [NOTICE](NOTICE). MasterGrid is acknowledged as prior inspiration, but IconGrid’s parameter contract, configuration resolution, geometry, rendering, and tests were independently written.
