# 0.1.0 release gate

Do not publish `0.1.0` until every automated and live item is checked. Never use
a production font for these tests, and never edit a `.glyphs` file directly
while it is open in Glyphs.

## Automated

- [x] Pure configuration and geometry tests, including odd/even center phase
- [x] Invalid-input and non-finite-value coverage
- [x] Numeric deterministic snapshots
- [x] Injected Glyphs/AppKit adapter tests
- [x] Core import isolation
- [x] Python syntax and bytecode compilation
- [x] Bundle/plist validation
- [x] Universal x86_64/arm64 wrapper validation
- [x] Static validation with `--target both`
- [x] Parameter-fixture coverage matches all 17 supported parameters
- [x] Installer dry-run, overwrite refusal, and forced replacement
- [x] Update plist, release notes, version, build, ZIP, and checksum agree
- [x] Static Pages build, links, screenshots, accessibility, and responsive rules
- [x] Local browser review at desktop and 390-pixel mobile widths
- [x] AI-client tabs work by pointer and keyboard
- [x] Dark-mode and reduced-motion media rules load without console warnings

## Glyphs 3.5 build 3530

- [x] Record Python runtime, MCP version, and macOS version
- [x] Open only disposable copies of the fixture matrix
- [x] Reporter appears as **View → Show Icon Grid**
- [x] Show the reporter and confirm a clean redraw
- [x] Confirm Regular uses 34-unit construction spacing
- [x] Confirm Bold uses 72-unit construction spacing
- [x] Read all fixture scopes and effective values through MCP
- [x] Dry-run, apply, and read back mutations through MCP
- [x] Preserve inactive and duplicate entries; refuse ambiguous duplicate mutation
- [x] Explicit save/reopen persists parameters on the designated disposable copy
- [x] Close all other disposable copies with changes discarded
- [ ] Confirm odd/even visually in Glyphs 3
- [ ] Confirm all nine origins and representative glyph widths live
- [ ] Confirm multiple zoom levels and light/dark appearance live
- [ ] Exercise Move, Draw, Pencil, Rectangle, and Circle alignment live
- [ ] Exercise crossings and every visible guide kind live
- [ ] Confirm passive Edit, lasso, Annotation, text, hand, and zoom exclusions live
- [ ] Inspect the Macro Panel after the complete interaction matrix

## Glyphs 4.0 build 3877

- [x] Record Python runtime, MCP version, and macOS version
- [x] Open only disposable copies for save/reopen validation
- [x] Reporter appears as **View → Show Icon Grid**
- [x] Show and hide the reporter
- [x] Confirm Regular uses 34-unit construction spacing
- [x] Confirm Bold uses 72-unit construction spacing
- [x] Confirm odd/even center phase visually
- [x] Read all fixture scopes and effective values through MCP
- [x] Dry-run, apply, and read back mutations through MCP
- [x] Confirm an MCP parameter edit redraws immediately
- [x] Preserve inactive and duplicate entries; refuse ambiguous duplicate mutation
- [x] Explicit save/reopen persists parameters on the designated disposable copy
- [x] Restore the tracked open fixture to Regular 34 / Bold 72 / implicit odd
- [x] Leave the tracked fixture unsaved
- [ ] Confirm all nine origins and representative glyph widths live
- [ ] Confirm multiple zoom levels and light/dark appearance live
- [ ] Exercise Move, Draw, Pencil, Rectangle, and Circle alignment live
- [ ] Exercise crossings and every visible guide kind live
- [ ] Confirm passive Edit, lasso, Annotation, text, hand, and zoom exclusions live
- [ ] Inspect the Macro Panel after the complete interaction matrix

## Current evidence

See [`docs/releases/0.1.0-test-report.md`](releases/0.1.0-test-report.md)
for the exact environment, fixture results, screenshots, and remaining blockers.

Static adapter tests cover the unchecked tool and guide combinations, but they
are not a substitute for the required live interaction pass in each Glyphs
version. The tag and public release remain blocked until those rows are checked.
