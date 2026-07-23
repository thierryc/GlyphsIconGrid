---
name: glyphs-mcp-icon-grid
description: Configure, inspect, reset, or troubleshoot GlyphsIconGrid custom parameters in an open Glyphs font through the local Glyphs MCP server. Use when a user asks to set `IconGrid.*` values, apply an icon-grid configuration, compare font and master overrides, or automate the reporter plug-in without saving the font.
---

# Glyphs MCP Icon Grid

Configure GlyphsIconGrid through the guarded generic custom-parameter tools in Glyphs MCP.

## Workflow

1. Connect to `http://127.0.0.1:9680/mcp/` with the Glyphs MCP **Edit** profile.
   If the endpoint refuses the connection or its tools disappear, stop instead of launching another Glyphs version automatically. Start the server in the intended app, then reload the client connection so it negotiates the tool list again.
2. Call `get_server_info`, then `list_open_fonts`. Confirm the expected Glyphs version owns the endpoint and identify the target by `familyName` and `filePath`; do not assume `font_index=0` when several fonts are open.
3. For master changes, call `get_font_masters` and resolve the exact `master_id` first.
4. Read current values with `get_custom_parameters`:
   - use `scope="font"` and `include_inactive=true` for font-level records;
   - use `scope="master"`, `master_id`, and `include_inactive=true` for one master's records;
   - use `scope="effective"` plus `master_id` to inspect master-over-font precedence;
   - always pass `prefix="IconGrid."`.
5. Read [references/parameters.md](references/parameters.md) and validate every requested value before writing.
6. Preview the exact change set with `set_custom_parameters`, `dry_run=true`, and the intended `scope`. Show the create, update, delete, and no-op actions to the user when the request did not already authorize those exact changes.
7. Immediately re-run `list_open_fonts` and confirm the target index still has the same `familyName` and `filePath` as the preview. Then apply an authorized preview with the same arguments plus `dry_run=false` and `confirm=true`.
8. Read back the target scope with `get_custom_parameters` and report the resulting values. State that Glyphs was redrawn and the font was not saved.

## Mutation rules

- If the target `.glyphs` file is open in Glyphs, never edit or patch that file on disk. Use Glyphs MCP for authorized changes, or close the document before any filesystem edit.
- Never call `save_font` unless the user separately asks to save.
- Use JSON `null` only when the user explicitly requests deletion or reset of a parameter.
- Do not replace a missing parameter with its default unless the user wants an explicit, portable value. Omitted parameters intentionally use the plug-in defaults.
- Stop on duplicate targeted parameters. Report the MCP duplicate error and ask the user to resolve the ambiguous records in Glyphs.
- Treat inactive target records as a blocker: changing their value does not necessarily enable them. Report the inactive record and ask whether to enable it manually in Glyphs or explicitly delete and recreate it.
- Keep font-level shared values and master-level exceptions separate. Do not flatten effective values back into both scopes.
- Preserve unrelated custom parameters and all glyph data.
- Prefer one batched `changes` object per scope over repeated single-parameter calls.
- For changes spanning multiple masters, preview every batch first and disclose that confirmed master applies are sequential rather than atomic.
- Glyphs 3 and Glyphs 4 may both be open. If the client reaches the wrong version, stop that version's MCP server normally: only one server can own shared port `9680`.

## Weight-matched master grid

- For the standard setup, leave font scope empty so appearance, placement, guides, and `gridMode=odd` use the built-in defaults.
- Set one `IconGrid.gridSize` value at master scope. It controls both square-cell size and the radial distance between concentric circles.
- For a 1000-UPM icon set, use `34` on Regular and `72` on Bold. Scale proportionally for another UPM when no master-specific unit was provided.
- Treat a valid `gridSize` as authoritative over `columns`, `rows`, and `rings`.
- Keep the default `IconGrid.gridMode = odd` for a cell centered on both construction axes. Use `even` only when grid borders must coincide with both axes. Store it at font scope unless a master needs a different phase.
- When asked to simplify a font, delete stored values that merely repeat defaults and count settings ignored by `gridSize`; preserve intentional non-default behavior unless the user requests the minimal two-parameter setup.

## Common calls

Inspect effective settings for a master:

```json
{
  "font_index": 0,
  "scope": "effective",
  "master_id": "MASTER-ID",
  "prefix": "IconGrid."
}
```

Preview the Regular master grid size:

```json
{
  "font_index": 0,
  "scope": "master",
  "master_id": "REGULAR-MASTER-ID",
  "changes": {
    "IconGrid.gridSize": 34
  },
  "dry_run": true,
  "confirm": false
}
```

Apply only after the preview is accepted by setting `dry_run=false` and `confirm=true` with the identical target and changes.
Repeat with the Bold master ID and `IconGrid.gridSize: 72`.

## Release verification

When validating this plug-in rather than configuring a user's font, follow [references/release-verification.md](references/release-verification.md). It uses closed tracked fixtures as sources, creates unique disposable copies, and never saves into the repository. A save/reopen check is allowed only on the manifest case explicitly marked `saveReopen: true`.

## Reporting

Report:

- target font, scope, and master when applicable;
- each parameter created, updated, deleted, or unchanged;
- the read-back result;
- `saved: false` unless the user explicitly requested a later save.
