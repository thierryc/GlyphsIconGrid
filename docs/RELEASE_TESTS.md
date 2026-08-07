# 0.2.0 release gate

Do not publish `0.2.0` until every automated and live item is checked. Never use
a production font for these tests, and never edit a `.glyphs` file directly
while it is open in Glyphs.

## Automated

- [x] Complete unit-test suite, including Mid Height lookup and fallback
- [x] Invalid-input, non-finite, and Glyphs missing-metric sentinel coverage
- [x] Numeric deterministic snapshots and geometry invariants
- [x] Injected Glyphs/AppKit adapter tests
- [x] Core import isolation
- [x] Python syntax and bytecode compilation
- [x] Bundle/plist validation at version `0.2.0`, build `4`
- [x] Universal x86_64/arm64 wrapper validation
- [x] Static validation with `--target both`
- [x] Parameter-fixture coverage matches all 17 supported parameters
- [x] Update plist, release notes, version, build, ZIP, and checksum agree
- [x] Static Pages build, links, screenshots, accessibility, and responsive rules
- [x] Release contract passes for tag `v0.2.0`

## Glyphs 3.5

- [x] Record the tested Glyphs build, Python runtime, MCP version, and macOS version
- [x] Open only disposable fixture copies
- [x] Reporter appears as **View → Show Icon Grid** and redraws cleanly
- [x] Regular and Bold inherit their 84- and 135-unit H stems
- [x] A Mid Height of `353` centers the complete construction system at `y=353`
- [x] The 1000-unit canvas bounds are `−147…853` with Mid Height `353`
- [x] Removing Mid Height restores baseline/cap-height midpoint centering at `y=350`
- [x] Filtered or invalid Mid Height values do not change the fallback center
- [x] Mid Height overshoot does not change the construction center
- [x] An explicit `IconGrid.baselineOffset` overrides Mid Height
- [x] The live/keyline diameter remains 875 units while its center moves
- [x] Odd/even phase, all nine origins, and representative glyph widths remain correct
- [x] Grid overflow, rings, spokes, keylines, and alignment feedback remain correct
- [x] Text, hand, zoom, Annotation, and passive Edit exclusions remain correct
- [x] Outlines remain unchanged and the reporter never saves implicitly
- [x] Inspect the Macro Panel after the complete interaction matrix

## Glyphs 4

- [x] Record the tested Glyphs build, Python runtime, MCP version, and macOS version
- [x] Open only disposable fixture copies
- [x] Reporter appears as **View → Show Icon Grid** and redraws cleanly
- [x] Regular and Bold inherit their 84- and 135-unit H stems
- [x] A Mid Height of `353` centers the complete construction system at `y=353`
- [x] The 1000-unit canvas bounds are `−147…853` with Mid Height `353`
- [x] Removing Mid Height restores baseline/cap-height midpoint centering at `y=350`
- [x] Filtered or invalid Mid Height values do not change the fallback center
- [x] Mid Height overshoot does not change the construction center
- [x] An explicit `IconGrid.baselineOffset` overrides Mid Height
- [x] The live/keyline diameter remains 875 units while its center moves
- [x] Odd/even phase, all nine origins, and representative glyph widths remain correct
- [x] Grid overflow, rings, spokes, keylines, and alignment feedback remain correct
- [x] Text, hand, zoom, Annotation, and passive Edit exclusions remain correct
- [x] Outlines remain unchanged and the reporter never saves implicitly
- [x] Inspect the Macro Panel after the complete interaction matrix

## Evidence

The exact environment, fixture results, screenshots, and release decision are
recorded in `docs/releases/0.2.0-test-report.md`.
Historical release reports remain unchanged.
