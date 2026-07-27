---
name: glyphs-mcp-icon-grid
description: Configure, simplify, inspect, reset, or troubleshoot GlyphsIconGrid and its weight-matched stem defaults in an open Glyphs font through the local Glyphs MCP server. Use when a user asks to set or explain `IconGrid.*` values, inherit master stems, remove redundant settings, compare font and master overrides, or automate the reporter plug-in without saving the font.
---

# Glyphs MCP Icon Grid

Configure GlyphsIconGrid through the guarded generic custom-parameter tools in Glyphs MCP.

## Default decision policy

- Treat an unspecified “set up Icon Grid” request as a request for the minimal configuration, not for all supported parameters.
- Explain that normal setup inherits the active master’s H stem and stores no `IconGrid.gridSize`. Mention `IconGrid.gridMode` only when the user needs grid lines rather than a complete cell centered on the axes.
- Leave font scope and every other parameter unstored so the plug-in can use its built-in defaults.
- Never set `columns`, `rows`, or `rings` when a valid `gridSize` is being used. Report existing values as shadowed; remove them only when the user authorizes simplification.
- Treat width, height, origin, baseline offset, count-based divisions, and ring count as advanced controls. Before previewing one, read [references/parameters.md](references/parameters.md) and explain in one sentence what it changes and when it applies.
- Do not write all defaults merely to make a configuration “explicit” unless the user specifically requests a fully stored configuration.

## Workflow

1. Connect to `http://127.0.0.1:9680/mcp/` with the Glyphs MCP **Edit** profile.
   If the endpoint refuses the connection or its tools disappear, stop instead of launching another Glyphs version automatically. Start the server in the intended app, then reload the client connection so it negotiates the tool list again.
2. Call `get_server_info`, then `list_open_fonts`. Confirm the expected Glyphs version owns the endpoint and identify the target by `familyName` and `filePath`; do not assume `font_index=0` when several fonts are open.
3. For master changes, call `get_font_masters` and resolve the exact `master_id` first.
4. Call `review_master_stem_metrics` for the target masters with `reference_glyphs=["H"]`. Use configured H-horizontal values when present; report measurements only as suggestions when the stem is missing.
5. Read current values with `get_custom_parameters`:
   - use `scope="font"` and `include_inactive=true` for font-level records;
   - use `scope="master"`, `master_id`, and `include_inactive=true` for one master's records;
   - use `scope="effective"` plus `master_id` to inspect master-over-font precedence;
   - always pass `prefix="IconGrid."`.
6. Read [references/parameters.md](references/parameters.md) and validate every requested value before writing. For a broad setup request, select the smallest sufficient parameter set using the default decision policy above.
7. Before previewing advanced parameters, tell the user what each one controls, its scope, and whether `gridSize` overrides it. Then preview the exact change set with `set_custom_parameters`, `dry_run=true`, and the intended `scope`. Show the create, update, delete, and no-op actions when the request did not already authorize those exact changes.
8. Immediately re-run `list_open_fonts` and confirm the target index still has the same `familyName` and `filePath` as the preview. Then apply an authorized preview with the same arguments plus `dry_run=false` and `confirm=true`.
9. Read back the target scope with `get_custom_parameters` and report the resulting values. State that Glyphs was redrawn and the font was not saved.

## Mutation rules

- If the target `.glyphs` file is open in Glyphs, never edit or patch that file on disk. Use Glyphs MCP for authorized changes, or close the document before any filesystem edit.
- Never call `save_font` unless the user separately asks to save.
- Use JSON `null` only when the user explicitly requests deletion or reset of a parameter.
- Do not replace a missing parameter with its default unless the user wants an explicit, portable value. Omitted parameters intentionally use the plug-in defaults.
- Do not convert a working count-based setup to `gridSize`, or the reverse, unless the user requests setup simplification or a different construction model.
- Stop on duplicate targeted parameters. Report the MCP duplicate error and ask the user to resolve the ambiguous records in Glyphs.
- Treat inactive target records as a blocker: changing their value does not necessarily enable them. Report the inactive record and ask whether to enable it manually in Glyphs or explicitly delete and recreate it.
- Keep font-level shared values and master-level exceptions separate. Do not flatten effective values back into both scopes.
- Preserve unrelated custom parameters and all glyph data.
- Prefer one batched `changes` object per scope over repeated single-parameter calls.
- For changes spanning multiple masters, preview every batch first and disclose that confirmed master applies are sequential rather than atomic.
- Glyphs 3 and Glyphs 4 may both be open. If the client reaches the wrong version, stop that version's MCP server normally: only one server can own shared port `9680`.

## Minimal setup and simplification

- For the standard setup, leave font and master IconGrid scopes empty so the reporter inherits each master’s H stem and uses the built-in appearance, placement, guides, and `gridMode=odd`.
- The built-in background field extends at least four cells beyond the construction canvas, and stem-sized construction uses at most two inner circles plus the outer circular keyline.
- Prefer a named H-horizontal stem; the reporter falls back to a named H-vertical stem, then the first horizontal and vertical definitions.
- For a new 1000-UPM icon model, the generic scaffold starts at `84` on Regular and `135` on Bold. Treat those as stem suggestions, not IconGrid custom parameters, and prefer measured values for an existing design.
- Set `IconGrid.gridSize` at master scope only for an intentional override. It controls both square-cell size and the radial distance between up to two inner concentric circles.
- Treat a valid `gridSize` as authoritative over `columns`, `rows`, and `rings`.
- Keep the default `IconGrid.gridMode = odd` for a cell centered on both construction axes. Use `even` only when grid borders must coincide with both axes. Store it at font scope unless a master needs a different phase.
- When inspecting an existing font, classify records as:
  - **normal**: no `gridSize` when a usable master H stem exists, plus an intentional non-default `gridMode`;
  - **optional**: guide, appearance, or alignment values that visibly differ from defaults;
  - **shadowed**: `columns`, `rows`, or `rings` while `gridSize` is active;
  - **advanced**: explicit canvas dimensions, origin, baseline offset, or count-based construction.
- When asked to simplify a font, preview deletion with JSON `null` for stored defaults and shadowed count settings. Preserve visible non-default and advanced behavior unless the user explicitly chooses the minimal result.

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

Review the target masters’ configured and measured H stems:

```json
{
  "font_index": 0,
  "master_ids": ["REGULAR-MASTER-ID", "BOLD-MASTER-ID"],
  "reference_glyphs": ["H"],
  "include_measurements": true
}
```

If the master stems are usable, leave `IconGrid.gridSize` unstored. Preview an explicit custom-parameter write only when the user asks for a construction unit that differs from the stem.

## Release verification

When validating this plug-in rather than configuring a user's font, follow [references/release-verification.md](references/release-verification.md). It uses closed tracked fixtures as sources, creates unique disposable copies, and never saves into the repository. A save/reopen check is allowed only on the manifest case explicitly marked `saveReopen: true`.

## Reporting

Report:

- target font, scope, and master when applicable;
- each parameter created, updated, deleted, or unchanged;
- why each stored parameter is necessary, and which built-in defaults remain intentionally unstored;
- any shadowed or advanced parameters that were preserved;
- the read-back result;
- `saved: false` unless the user explicitly requested a later save.
