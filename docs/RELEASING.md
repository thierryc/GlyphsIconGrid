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

Review both ZIPs and their checksums. Confirm that the main archive contains the plug-in bundle, complete `skills/glyphs-mcp-icon-grid` directory, and executable `Install GlyphsIconGrid Skill.command`. Confirm that `GlyphsIconGrid-Skill.zip` contains only the complete skill, installer, license, and notice. Confirm that the version in the bundle, update plist, changelog, release notes, and intended tag agree.

## 2. Live gate

Follow [the release checklist](RELEASE_TESTS.md) in current Glyphs 3.5 and Glyphs 4 builds. Use disposable fixture copies and one MCP server at a time. Record the actual builds, Python runtimes, macOS version, screenshots, and results in the versioned test report.

Do not treat static validation as proof of live compatibility. Do not tag while any required row remains unchecked.

## 3. Publish

Merge the reviewed release branch to `main`. Rebuild the site locally, publish
the exact `build/site` output to the `gh-pages` branch, and configure GitHub
Pages to serve `/` from that branch. Verify the public update plist after the
branch deployment finishes.

Create an annotated tag on the exact validated source commit:

```sh
git tag -a v0.1.1 -m "GlyphsIconGrid 0.1.1"
git push origin v0.1.1
```

Create the release from the locally validated archive:

```sh
gh release create v0.1.1 \
  dist/GlyphsIconGrid-0.1.1.zip \
  dist/GlyphsIconGrid-0.1.1.zip.sha256 \
  dist/GlyphsIconGrid-Skill.zip \
  dist/GlyphsIconGrid-Skill.zip.sha256 \
  --verify-tag \
  --title "GlyphsIconGrid 0.1.1" \
  --notes-file docs/releases/0.1.1.md
```

Verify both published ZIPs and their SHA-256 assets after upload. GitHub Actions are not
part of this release process.

## 4. Package directory

Only after the release and screenshot URLs are public, add the plug-in to the end of the `plugins` array on the `glyphs3` branch of `thierryc/glyphs-packages`. Run that repository's parser and tests, then confirm installation from the alternate package repository in both supported Glyphs versions before opening the upstream pull request.
