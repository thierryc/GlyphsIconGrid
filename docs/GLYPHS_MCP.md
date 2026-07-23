# Configuring GlyphsIconGrid with Glyphs MCP

GlyphsIconGrid stores its configuration as `IconGrid.*` custom parameters, so the local [Glyphs MCP server](https://github.com/thierryc/Glyphs-mcp) can inspect and edit the same values shown in Font Info. The repository includes a guarded skill at [`skills/glyphs-mcp-icon-grid`](../skills/glyphs-mcp-icon-grid/SKILL.md) for this workflow.

Glyphs MCP changes the open document in memory and asks Glyphs to redraw. It does not save the font automatically.

## Connect to the intended Glyphs version

Glyphs 3 and Glyphs 4 may both be open, but their MCP plug-ins share local port `9680`. Only one server can own that port at a time.

1. In the intended version, choose **Edit → Glyphs MCP Server Status…** and start the server.
2. Select the MCP **Edit** tool profile. The read-only profile can inspect parameters but does not expose `set_custom_parameters`.
3. Configure the client for a direct Streamable HTTP connection to `http://127.0.0.1:9680/mcp/`.
4. Reload the MCP connection or start a new task after changing profiles so the client receives the updated tool list.
5. Call `get_server_info`, then `list_open_fonts`. Verify the Glyphs version and identify the target font by both `familyName` and `filePath`.

Do not assume `font_index: 0` when more than one document is open. Font indexes can also change as documents open or close.

## Use the repository skill

The skill directory is:

```text
skills/glyphs-mcp-icon-grid/
```

Keep that directory intact so `SKILL.md`, `agents/openai.yaml`, and `references/parameters.md` remain together. Invoke it as `$glyphs-mcp-icon-grid` when the client supports named skills.

Preview and install it with the repository helper:

```sh
python3 scripts/install_skill.py --client codex --scope user --dry-run
python3 scripts/install_skill.py --client codex --scope user
```

The supported user locations are:

| Client | Skill location | MCP configuration |
| --- | --- | --- |
| Codex Desktop/CLI | `~/.agents/skills/glyphs-mcp-icon-grid` | `~/.codex/config.toml` |
| Claude Code | `~/.claude/skills/glyphs-mcp-icon-grid` | `claude mcp add` |
| Gemini CLI | `~/.agents/skills/glyphs-mcp-icon-grid` | `~/.gemini/settings.json` |
| Cursor | `~/.agents/skills/glyphs-mcp-icon-grid` | `~/.cursor/mcp.json` |

For project scope, Codex, Gemini, and Cursor use `.agents/skills`; Claude Code uses `.claude/skills`.

### MCP client examples

Codex `config.toml`:

```toml
[mcp_servers.glyphs-mcp]
url = "http://127.0.0.1:9680/mcp/"
```

Claude Code:

```sh
claude mcp add --scope user --transport http glyphs-mcp http://127.0.0.1:9680/mcp/
```

Gemini CLI `settings.json`:

```json
{
  "mcpServers": {
    "glyphs-mcp": {
      "httpUrl": "http://127.0.0.1:9680/mcp/"
    }
  }
}
```

Cursor `mcp.json`:

```json
{
  "mcpServers": {
    "glyphs-mcp": {
      "url": "http://127.0.0.1:9680/mcp/"
    }
  }
}
```

The [Glyphs MCP installer](https://github.com/thierryc/Glyphs-mcp) is the recommended way to install and start the server. The helper in this repository installs only the Icon Grid workflow skill and intentionally does not overwrite client MCP settings. Browser-only AI sessions normally cannot connect to a server bound to `127.0.0.1` on your Mac.

The skill enforces this sequence:

1. verify the server and target font;
2. resolve the exact master ID when master scope is involved;
3. read font, master, or effective values, including inactive records;
4. validate requested values against the [parameter schema](../skills/glyphs-mcp-icon-grid/references/parameters.md);
5. preview the complete change set with `dry_run: true`;
6. re-identify the font before mutation;
7. apply the identical change set only with `dry_run: false` and `confirm: true`;
8. read the scope back and report `saved: false`.

The generic MCP calls below can also be used directly.

## Inspect parameters safely

Start with server and document discovery:

```json
{}
```

Use that empty argument object first with `get_server_info` and then with `list_open_fonts`. For a master-level request, resolve IDs with `get_font_masters`:

```json
{
  "font_index": 0
}
```

Read all IconGrid records at font scope:

```json
{
  "font_index": 0,
  "scope": "font",
  "prefix": "IconGrid.",
  "include_inactive": true
}
```

Read records stored on one master:

```json
{
  "font_index": 0,
  "scope": "master",
  "master_id": "MASTER-ID",
  "prefix": "IconGrid.",
  "include_inactive": true
}
```

Read the values that are actually effective after master-over-font inheritance:

```json
{
  "font_index": 0,
  "scope": "effective",
  "master_id": "MASTER-ID",
  "prefix": "IconGrid."
}
```

Use these objects with `get_custom_parameters`. Reading `font`, `master`, and `effective` separately prevents an inherited value from being mistaken for a stored master override.

## Preview, confirm, and read back

Preview the Regular master’s single grid-size parameter with `set_custom_parameters`:

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

Inspect the returned create, update, delete, and no-op actions. Immediately call `list_open_fonts` again and confirm that the same index still identifies the same `familyName` and `filePath`.

To apply, repeat the complete call above with the identical target and `changes` object, changing only `dry_run` to `false` and `confirm` to `true`.

Then call `get_custom_parameters` again for the written scope. Report the read-back values and `saved: false`. The operation requests a redraw, but saving remains a separate user decision in Glyphs. Call a save tool only when the user explicitly asks to save.

Repeat the same preview/apply/read-back sequence with the Bold master ID and `IconGrid.gridSize: 72`. When changing several masters, preview every batch first. Confirmed master writes happen sequentially and are not a single atomic transaction.

## Delete a value and restore inheritance

JSON `null` means delete the named custom-parameter record; it does not mean set the parameter's value to null.

Preview removal of a master override:

```json
{
  "font_index": 0,
  "scope": "master",
  "master_id": "MASTER-ID",
  "changes": {
    "IconGrid.gridSize": null
  },
  "dry_run": true,
  "confirm": false
}
```

After confirmed deletion, that master inherits `IconGrid.gridSize` from the font. If the font has no active valid record either, the plug-in uses its built-in count-based defaults. Deleting a font record does not remove a master override.

Use `null` only for an explicitly requested reset or deletion. A missing value is meaningful: do not write every default merely because no record exists.

## Guardrails and edge cases

- Never edit or patch a `.glyphs` file on disk while that document is open in Glyphs. Use Glyphs MCP for authorized changes, or close the document before editing the file directly.
- Preserve unrelated custom parameters and all glyph data.
- Keep shared font values and master exceptions in their separate scopes; do not copy resolved effective values into both.
- Stop if the MCP tool reports duplicate records for a targeted parameter. Resolve the ambiguity in Glyphs before retrying.
- Treat an inactive targeted record as a decision point. Editing its value may not enable it; either enable it manually or explicitly delete and recreate it.
- Validate every value before previewing. The accepted names, ranges, colors, booleans, and origins are listed in [Custom parameter reference](PARAMETERS.md).
- Prefer one batched `changes` object per scope so the preview accurately describes the intended operation.
- Never save or close unrelated open documents as part of parameter configuration.

## Example prompts

Use prompts that identify the target document, scope, and save policy:

- “Use `$glyphs-mcp-icon-grid` to inspect the effective IconGrid settings for the Regular master of `IconGrid-Test.glyphs`. Do not change or save anything.”
- “For this 1000-UPM icon set, leave font scope empty and set only `IconGrid.gridSize` to `34` on Regular and `72` on Bold. Preview both master batches first, read them back, and do not save the font.”
- “Remove stored IconGrid values that merely repeat plug-in defaults, plus count settings ignored by a master `gridSize`. Preview every deletion and leave the document unsaved.”
- “Compare font, master, and effective `IconGrid.*` values for every master, including inactive records. Report duplicates or invalid values without fixing them.”
