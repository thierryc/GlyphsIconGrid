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

- [x] Record Python runtime and macOS version
- [x] Install disposable plug-in copy and open `tests/fixtures/IconGrid-Test.glyphs`
- [x] Reporter appears only as **View → Show Icon Grid**
- [ ] Show/hide, all origins, both masters, fixed grid across glyph widths, zooms, light/dark appearance
- [ ] Glyphs MCP parameter edit redraws immediately
- [ ] Explicit save/reopen preserves parameters
- [ ] No Macro Panel exception, outline/snapping change, or implicit save
- [x] Remove only the disposable test installation

## Glyphs 4.0 build 3875

- [x] Record Python runtime and macOS version
- [x] Install disposable plug-in copy and open `tests/fixtures/IconGrid-Test.glyphs`
- [ ] Reporter appears only as **View → Show Icon Grid**
- [ ] Show/hide, all origins, both masters, fixed grid across glyph widths, zooms, light/dark appearance
- [ ] Glyphs MCP parameter edit redraws immediately
- [ ] Explicit save/reopen preserves parameters
- [ ] No Macro Panel exception, outline/snapping change, or implicit save
- [x] Remove only the disposable test installation

## Evidence

| Item | Value |
| --- | --- |
| Test fixture commit | `7cbfa7a` |
| Live bundle commit | `126c62f` |
| Glyphs 3 | 3.5 (3530), Python 3.12.3; fixed 1500-unit grid rendered on 1000- and 800-unit advances |
| Glyphs 4 | 4.0 (3875), Python 3.14.6; clean final reporter check pending application restart |
| macOS | 26.6 (25G5065a) |
| Release ZIP installs | Pending both live validations |

Glyphs 4 exposed that its loader requires the official template's executable
mode on `Contents/Resources/plugin.py`. Commit `126c62f` restores mode `0755`
and adds both a unit-test assertion and a static-validator check. A final clean
Glyphs 4 restart is still required because another process had a production
font open during this test session; that process was not restarted or saved.
