# Releasing GlyphsIconGrid

Never publish from an uncommitted worktree or edit a `.glyphs` file directly while it is open in Glyphs.

## 1. Automated gate

```sh
python3 -m unittest discover -v
python3 -m compileall -q IconGrid.glyphsReporter tests scripts
python3 scripts/validate.py IconGrid.glyphsReporter --target both
python3 scripts/package.py
python3 scripts/release_check.py --require-artifacts
python3 scripts/build_site.py
```

Review the ZIP contents and checksum. Confirm that the version in the bundle, update plist, changelog, release notes, and intended tag agree.

## 2. Live gate

Follow [the release checklist](RELEASE_TESTS.md) in current Glyphs 3.5 and Glyphs 4 builds. Use disposable fixture copies and one MCP server at a time. Record the actual builds, Python runtimes, macOS version, screenshots, and results in the versioned test report.

Do not treat static validation as proof of live compatibility. Do not tag while any required row remains unchecked.

## 3. Publish

Merge the reviewed release branch to `main`, wait for CI and Pages to pass, and verify the public update plist. Create an annotated tag on that exact commit:

```sh
git tag -a v0.1.0 -m "GlyphsIconGrid 0.1.0"
git push origin v0.1.0
```

The tag workflow rebuilds the archive, verifies the tag/version contract, and creates the GitHub release. Verify the release ZIP and SHA-256 asset after the workflow completes.

## 4. Package directory

Only after the release and screenshot URLs are public, add the plug-in to the end of the `plugins` array on the `glyphs3` branch of `thierryc/glyphs-packages`. Run that repository's parser and tests, then confirm installation from the alternate package repository in both supported Glyphs versions before opening the upstream pull request.
