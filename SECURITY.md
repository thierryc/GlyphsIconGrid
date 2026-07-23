# Security policy

## Supported versions

The latest published release receives security and compatibility fixes. Pre-release branches and source checkouts are supported on a best-effort basis.

## Report a vulnerability

Please use the repository's private **Security → Report a vulnerability** form. Do not open a public issue for a vulnerability that could expose user files, execute unintended code, or weaken the local Glyphs MCP confirmation model.

Include the Glyphs version, macOS version, plug-in version, reproduction steps, and whether Glyphs MCP was running. You should receive an acknowledgement within seven days.

GlyphsIconGrid draws guides and reads custom parameters. It should never save a document implicitly, edit outlines, or transmit font data. Treat any behavior that contradicts those guarantees as security-relevant.
