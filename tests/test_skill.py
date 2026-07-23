from __future__ import absolute_import

import os
import re
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "glyphs-mcp-icon-grid")


def read(relative_path):
    with open(os.path.join(SKILL, relative_path), "r", encoding="utf-8") as handle:
        return handle.read()


class GlyphsMcpIconGridSkillTests(unittest.TestCase):
    def test_skill_identity_and_safety_contract(self):
        source = read("SKILL.md")
        self.assertTrue(source.startswith("---\nname: glyphs-mcp-icon-grid\n"))
        self.assertIn("get_server_info", source)
        self.assertIn("list_open_fonts", source)
        self.assertIn("get_custom_parameters", source)
        self.assertIn("set_custom_parameters", source)
        self.assertIn("dry_run=true", source)
        self.assertIn("dry_run=false", source)
        self.assertIn("confirm=true", source)
        self.assertIn("never edit or patch that file on disk", source)
        self.assertIn("Never call `save_font`", source)
        self.assertNotIn("Ensure only the intended Glyphs major version is running", source)
        self.assertIn("use `34` on Regular and `72` on Bold", source)
        self.assertIn("default `IconGrid.gridMode = odd`", source)
        self.assertIn("references/release-verification.md", source)

    def test_openai_metadata_declares_local_glyphs_mcp_dependency(self):
        source = read(os.path.join("agents", "openai.yaml"))
        self.assertIn('display_name: "Glyphs MCP Icon Grid"', source)
        self.assertIn('value: "glyphs_mcp_server"', source)
        self.assertIn('url: "http://127.0.0.1:9680/mcp/"', source)

    def test_reference_lists_every_supported_parameter_once(self):
        source = read(os.path.join("references", "parameters.md"))
        names = re.findall(r"\| `(IconGrid\.[A-Za-z]+)` \|", source)
        self.assertEqual(
            names,
            [
                "IconGrid.columns",
                "IconGrid.rows",
                "IconGrid.gridSize",
                "IconGrid.gridMode",
                "IconGrid.width",
                "IconGrid.height",
                "IconGrid.origin",
                "IconGrid.baselineOffset",
                "IconGrid.padding",
                "IconGrid.majorEvery",
                "IconGrid.rings",
                "IconGrid.spokes",
                "IconGrid.showKeylines",
                "IconGrid.color",
                "IconGrid.opacity",
                "IconGrid.alignmentHighlight",
                "IconGrid.alignmentTolerance",
            ],
        )


if __name__ == "__main__":
    unittest.main()
