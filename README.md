# GlyphsIconGrid

[![Tests](https://github.com/thierryc/GlyphsIconGrid/actions/workflows/test.yml/badge.svg)](https://github.com/thierryc/GlyphsIconGrid/actions/workflows/test.yml)
[![Pages](https://github.com/thierryc/GlyphsIconGrid/actions/workflows/pages.yml/badge.svg)](https://thierryc.github.io/GlyphsIconGrid/)
[![Glyphs 3.5 and 4](https://img.shields.io/badge/Glyphs-3.5%20and%204-7c4dff)](https://glyphsapp.com/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)

GlyphsIconGrid is a no-dialog reporter plug-in that draws an icon construction system behind the active glyph in Glyphs 3 and Glyphs 4. It adds a font-aligned square grid, circular guides, radial spokes, and common icon keylines without changing outlines, snapping, exports, or saving the document.

Visit the [GlyphsIconGrid website](https://thierryc.github.io/GlyphsIconGrid/) for the visual setup guide.

![Glyphs 4 Edit view showing a lightbulb icon over the expanded stem grid and enlarged metric-fitted keylines.](docs/images/icon-grid-overview.png)

## Features

- A 24 × 24 one-em square construction canvas by default.
- Horizontal centering on the glyph advance and vertical centering between the baseline and cap height.
- An expanded background grid that reaches four stem-sized cells beyond the icon square in every direction.
- A cell-centered `odd` grid by default, with an optional line-centered `even` mode.
- Metric-fitted live area, up to two stem-spaced inner circles, radial spokes, and Material-derived circle, square, portrait, and landscape keylines.
- A weight-aware default that uses the active master’s capital-H stem for both square cells and circular spacing.
- Blue guides that remain visually distinct from Glyphs metric and user guides.
- Strict alignment feedback near a guide while drawing, shaping, or moving nodes; it never acts as snapping.
- Font-level custom parameters with optional per-master overrides.

## Install

1. Download a ZIP from [Releases](https://github.com/thierryc/GlyphsIconGrid/releases) and extract it.
2. Double-click `IconGrid.glyphsReporter`, or move it into the plug-in folder for the Glyphs version you use.
3. Restart Glyphs.
4. Open a glyph in Edit view and choose **View → Show Icon Grid**.

The source bundle is validated for Glyphs 3.5 and Glyphs 4. See the [release test checklist](docs/RELEASE_TESTS.md) for the exact automated and live checks.

## Configure

No `IconGrid.*` parameter is required when the font has stem metrics:

1. Open **File → Font Info → Masters → Stems**.
2. Add or verify the capital-H horizontal stem for every master.
3. Choose **View → Show Icon Grid**.

The reporter prefers a named H horizontal stem, then a named H vertical stem, and follows the selected master automatically. The attached research scaffold gives `84` for Regular and `135` for Bold at 1000 UPM; use measured values when the design already exists.

The grid value is the stem itself. Its relationship to the default Glyphs cap-height span is:

```text
cap-height cells = (cap height − baseline) / H stem
```

With the default 700-unit cap height, the 84-unit Regular stem spans 8.33 cells and the 135-unit Bold stem spans 5.19 cells. Set `IconGrid.gridSize` only when you need an explicit override. The default `odd` mode centers one grid cell on the construction axes; add `IconGrid.gridMode = even` only when the axes should coincide with grid lines.

The unstored live/keyline diameter is `cap height / 0.8`: 875 units for the default 700-unit cap height. This makes the Material landscape rectangle run exactly from baseline to cap height. Store `IconGrid.padding` only when you intentionally want a cell-based inset instead.

All other settings are optional. The [plain-language parameter guide](docs/PARAMETERS.md) separates the two normal controls from guide, appearance, and advanced compatibility options. See the [human user guide](docs/USER_GUIDE.md) for recipes and troubleshooting.

## Glyphs MCP automation

Every release includes the distributable [`glyphs-mcp-icon-grid` skill](skills/glyphs-mcp-icon-grid/SKILL.md). It inspects font and master scopes, validates every `IconGrid.*` value, previews writes, removes redundant settings safely, reads the result back, and never saves the font implicitly.

Connect the Glyphs MCP **Edit** profile and verify the target font before changing it. The [Glyphs MCP guide](docs/GLYPHS_MCP.md) covers installation, safe calls, inheritance, and example prompts.

On a Mac, download and unzip the release, then double-click `Install GlyphsIconGrid Skill.command`. Choose the shared location for Codex, Gemini, and Cursor; choose Claude for `~/.claude/skills`; or install both. The installer uses built-in macOS tools, requires no repository checkout or Python installation, and keeps a dated backup before replacing an existing copy.

For a source checkout, the command-line helper remains available:

```sh
python3 scripts/install_skill.py --client codex --scope user --dry-run
python3 scripts/install_skill.py --client codex --scope user
```

Replace `codex` with `claude`, `gemini`, or `cursor`. The first command previews the destination; the second copies the complete skill directory.

## Documentation

- [User guide](docs/USER_GUIDE.md)
- [Custom parameter reference](docs/PARAMETERS.md)
- [Glyphs MCP automation](docs/GLYPHS_MCP.md)
- [Behavioral specification](docs/SPECIFICATION.md)
- [Release test checklist](docs/RELEASE_TESTS.md)
- [Release process](docs/RELEASING.md)
- [Changelog](CHANGELOG.md)
- [Contributing](CONTRIBUTING.md)
- [Tracked test fixture](tests/fixtures/README.md)

## Develop and test

The configuration, geometry, and interaction core imports neither Glyphs nor AppKit, so the deterministic suite runs with standard Python:

```sh
python3 -m unittest discover -v
python3 -m compileall -q IconGrid.glyphsReporter tests scripts
python3 scripts/validate.py IconGrid.glyphsReporter --target both
python3 scripts/package.py
```

CI runs the unit, compile, static bundle, dual-target, and packaging checks. Live UI behavior is covered separately by the release checklist. The tracked fixture at `tests/fixtures/IconGrid-Test.glyphs` contains the `/lightbulb` artwork and two masters used by the documentation and manual tests.

## License and attribution

GlyphsIconGrid is licensed under [Apache-2.0](LICENSE). The official GlyphsSDK reporter template and universal wrapper are attributed in [NOTICE](NOTICE). MasterGrid is acknowledged as prior inspiration; GlyphsIconGrid’s parameter contract, configuration resolution, geometry, rendering, and tests were independently written.
