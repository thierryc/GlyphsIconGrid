# 0.1.0 release gate

Do not publish `0.1.0` until every automated and live item is checked. Never use a production font for these tests.

## Automated

- [x] Pure configuration and geometry tests
- [x] Invalid-input and non-finite-value coverage
- [x] Numeric deterministic snapshots
- [x] Injected Glyphs/AppKit adapter tests
- [x] Core import isolation
- [x] Python syntax and bytecode compilation
- [x] Bundle/plist validation
- [x] Universal x86_64/arm64 wrapper validation
- [x] Static validation with `--target both`

## Glyphs 3.5 build 3530

- [ ] Record Python runtime and macOS version
- [ ] Install disposable plug-in copy and open `tests/fixtures/IconGrid-Test.glyphs`
- [ ] Reporter appears only as **View → Show Icon Grid**
- [ ] Show/hide, all origins, both masters, fixed grid across glyph widths, zooms, light/dark appearance
- [ ] Glyphs MCP parameter edit redraws immediately
- [ ] Explicit save/reopen preserves parameters
- [ ] No Macro Panel exception, outline/snapping change, or implicit save
- [ ] Remove only the disposable test installation

## Glyphs 4.0 build 3875

- [ ] Record Python runtime and macOS version
- [ ] Install disposable plug-in copy and open `tests/fixtures/IconGrid-Test.glyphs`
- [ ] Reporter appears only as **View → Show Icon Grid**
- [ ] Show/hide, all origins, both masters, fixed grid across glyph widths, zooms, light/dark appearance
- [ ] Glyphs MCP parameter edit redraws immediately
- [ ] Explicit save/reopen preserves parameters
- [ ] No Macro Panel exception, outline/snapping change, or implicit save
- [ ] Remove only the disposable test installation

## Evidence

| Item | Value |
| --- | --- |
| Test fixture commit | `4669067` |
| Glyphs 3 | 3.5 (3530), runtime pending |
| Glyphs 4 | 4.0 (3875), runtime pending |
| macOS | 26.6 (25G5065a) |
| Release ZIP installs | Pending both live validations |
