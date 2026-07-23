# Contributing to GlyphsIconGrid

GlyphsIconGrid keeps its geometry and configuration logic independent from Glyphs and AppKit so most changes can be tested without launching Glyphs. Live checks are still required for changes to the reporter adapter, drawing, tool-state detection, or Glyphs MCP integration.

## Development environment

You need:

- macOS for live testing in Glyphs;
- Glyphs 3.5 and/or Glyphs 4 for plug-in testing;
- Python 3.9 or newer for the automated checks; and
- Git.

No third-party Python package is required for the repository test suite. Start from the repository root:

```sh
git status --short
python3 -m unittest discover -v
```

The working tree may contain unrelated user changes. Do not reset, replace, stage, or save files that are outside the change you are making.

## Link a working bundle safely

For live development, link the bundle from this checkout into the plug-in folder for the Glyphs version being tested. The following example targets Glyphs 4:

```sh
repo_root="$(pwd -P)"
bundle="$repo_root/IconGrid.glyphsReporter"
plugins_dir="$HOME/Library/Application Support/Glyphs 4/Plugins"
destination="$plugins_dir/IconGrid.glyphsReporter"

mkdir -p "$plugins_dir"
if [ -e "$destination" ] || [ -L "$destination" ]; then
  echo "Stop: $destination already exists; inspect it before continuing."
else
  ln -s "$bundle" "$destination"
fi
```

Replace `Glyphs 4` with `Glyphs 3` to target Glyphs 3. Never overwrite an existing installation automatically. Restart the application after linking the bundle, once any unrelated open documents are safe.

Remove only a development link that you have verified is a symbolic link:

```sh
if [ -L "$destination" ]; then
  unlink "$destination"
fi
```

Do not use a recursive deletion command for a plug-in path.

## Run the checks

Run the same core commands used by GitHub Actions:

```sh
python3 -m unittest discover -v
python3 -m compileall -q IconGrid.glyphsReporter tests scripts
python3 scripts/validate.py IconGrid.glyphsReporter --target both
python3 scripts/package.py
```

The validator checks the bundle identity, Python syntax, principal class, executable entry points, official universal SDK wrapper, and the static Glyphs 3/4 contract. It does not launch either Glyphs version. `scripts/package.py` writes the deterministic release archive to `dist/`; generated archives are ignored by Git.

Use [docs/RELEASE_TESTS.md](docs/RELEASE_TESTS.md) for live release checks. Test only with disposable or repository-owned fixtures, never a production font.

## Use Glyphs MCP safely

Glyphs 3 and Glyphs 4 expose their MCP servers on the same local port, `9680`. Both applications may be open, but only one MCP server can own the port. Before an MCP session, confirm which process owns it:

```sh
lsof -nP -iTCP:9680 -sTCP:LISTEN
```

If the wrong Glyphs version owns it, stop that server normally before starting the intended one. Do not kill an unidentified process. Reconnect the MCP client after changing server ownership.

Parameter mutations should be previewed with the MCP dry-run mode first and applied only with explicit confirmation. Glyphs MCP parameter tools request a redraw but do not save the document; keep that behavior and never save or close unrelated documents as part of a test.

## Fixture policy

[`tests/fixtures/IconGrid-Test.glyphs`](tests/fixtures/IconGrid-Test.glyphs) is a tracked test asset, not a disposable build product. Preserve its `/lightbulb` glyph, two masters, and intentional custom-parameter coverage unless a test change specifically requires updating them. See [the fixture README](tests/fixtures/README.md) for its structure and screenshot workflow.

Never edit or patch a `.glyphs` file on disk while it is open in Glyphs. Make authorized live-document changes through Glyphs MCP, or close the document before editing the file directly. Concurrent application and filesystem edits can trigger reload conflicts and discard in-memory work.

Glyphs may create sibling files named like `IconGrid-Test (Autosaved).glyphs`. They are local recovery artifacts and are ignored by this rule:

```gitignore
tests/fixtures/* (Autosaved).glyphs
```

Do not force-add an autosaved sibling. If it contains a useful change, inspect it and intentionally reproduce only that change in the tracked fixture. Do not delete someone else’s autosave without their permission.

## Pull-request checklist

- Keep the change focused and preserve unrelated working-tree edits.
- Add or update deterministic tests for behavior changes.
- Run the unit tests, bytecode compilation, dual-version static validation, and packaging commands above.
- Perform the relevant Glyphs 3 and Glyphs 4 live checks when adapter or UI behavior changes, one MCP host at a time.
- Update parameter, behavior, fixture, or user documentation when the public contract changes.
- Confirm that no autosaved fixture, `dist/` archive, cache, or local installation link is included.
- Review `git diff` and `git status --short` before opening the pull request.
