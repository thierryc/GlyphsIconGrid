# IconGrid test fixture

`IconGrid-Test.glyphs` is the tracked visual and integration fixture for GlyphsIconGrid. It is safe to use for plug-in tests and documentation screenshots; do not substitute a production font.

## Contents

- The displayed glyph is `/lightbulb`.
- The `Regular` and `Bold` masters both use a 1000-unit glyph advance so the two drawings can be compared against the same font-aligned construction canvas.
- Font scope contains no `IconGrid.*` records; all shared behavior comes from the plug-in defaults.
- The fixture relies on the built-in `odd` grid mode, with one cell centered on the construction axes.
- `Regular` defines an 84-unit H horizontal stem.
- `Bold` defines a 135-unit H horizontal stem.

This parameter-free IconGrid setup verifies exact weight-matched Regular/Bold cell and circle spacing inherited from native Glyphs stem metrics.

Never edit or patch the tracked `.glyphs` file on disk while it is open in Glyphs. Use Glyphs MCP for authorized live-document changes, or close the document before editing the file directly.

## Prepare a README screenshot

1. Confirm that the Glyphs version being tested owns MCP port `9680`. Both applications may be open, but only one MCP server can own the shared port.
2. Open the tracked `IconGrid-Test.glyphs`, not an autosaved sibling, and select `/lightbulb` in an Edit tab.
3. Select the `Regular` master and enable **View → Show Icon Grid**.
4. Choose the Select/Edit tool and clear the node selection. Turn off path-order or compatibility overlays, measurements, annotations, background layers, and other temporary drawing aids.
5. Use a neutral, high-contrast appearance and frame the glyph at a useful working zoom. Keep enough Glyphs interface visible to establish context, while showing the expanded construction field and at least four overflow cells on every side.
6. Verify that the cells are square, one cell is centered across both construction axes, the field is horizontally centered on the glyph advance, and its vertical center sits halfway between the baseline and cap height. Confirm at most two stem-spaced inner circles plus the outer circular keyline. The blue grid should remain visibly distinct from Glyphs metric guides.
7. Capture a clean PNG at `docs/images/icon-grid-overview.png`; GitHub will scale it to the README width. Keep the repository image approximately 1800 pixels wide and use the sRGB color profile for predictable browser rendering.
8. Inspect the image at full size for selected nodes, colored compatibility shapes, connector rays, path numbers, unrelated windows, or private information before using it in the README.

Suggested alternative text:

> Glyphs 4 Edit view with GlyphsIconGrid’s blue square grid, circular guides, spokes, and keylines behind a lightbulb glyph.

The screenshot setup is view state. Do not save incidental tab, selection, zoom, or overlay changes into the tracked fixture merely to capture the image.

## Autosaved siblings

Glyphs can create a local recovery file such as `IconGrid-Test (Autosaved).glyphs`. The repository ignores files matching:

```gitignore
tests/fixtures/* (Autosaved).glyphs
```

These files are ignored because they reflect a local application session and can contain incidental view or recovery state; they are not an alternate fixture source. Preserve an autosave when someone may still need it, never force-add it to Git, and never use it for the canonical README screenshot. If it contains intentional outline or parameter work, review the difference and apply only the wanted changes to `IconGrid-Test.glyphs` explicitly.
