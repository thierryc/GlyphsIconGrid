# Release verification workflow

Use this workflow only for the GlyphsIconGrid release fixture matrix.

1. Confirm the tracked fixture is closed before preparing a copy. Never modify a tracked `.glyphs` file while it is open.
2. Create a unique temporary directory and copy one fixture into it. Treat that copy as disposable.
3. In the Glyphs version being tested, start Glyphs MCP with the **Edit** profile.
4. Call `get_server_info` and `list_open_fonts`; confirm the app version and the temporary file path.
5. Call `get_font_masters`, then read font, master, and effective `IconGrid.*` records with `include_inactive=true`.
6. Compare the result with `tests/fixtures/parameter-matrix.json`.
7. Preview each manifest mutation with `dry_run=true`.
8. Re-identify the open font, apply the identical changes with `dry_run=false` and `confirm=true`, then read back every changed scope.
9. Confirm immediate reporter redraw and that the font remains unsaved.
10. Only for the case marked `saveReopen: true`, explicitly save the temporary copy, close it, reopen it, and repeat the read-back.
11. Close or discard the copy. Preserve tracked fixtures and unrelated open documents.
12. Repeat with the other supported Glyphs major version after confirming which server owns port `9680`.

Stop rather than mutating a targeted duplicate or inactive record. Those cases exist to verify the guardrails and must produce the expected blocker.
