from __future__ import absolute_import

import os
import re
import struct
import unittest

from scripts import build_site


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_resolve(self):
        missing = []
        for directory, subdirectories, filenames in os.walk(ROOT):
            subdirectories[:] = sorted(
                name
                for name in subdirectories
                if name not in (".git", "build", "dist", "__pycache__")
            )
            for filename in sorted(filenames):
                if not filename.endswith(".md"):
                    continue
                source_path = os.path.join(directory, filename)
                with open(source_path, "r", encoding="utf-8") as handle:
                    source = handle.read()
                for raw_target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", source):
                    target = raw_target.strip().split()[0].strip("<>")
                    if target.startswith(("#", "http://", "https://", "mailto:")):
                        continue
                    target = target.split("#", 1)[0]
                    resolved = os.path.normpath(os.path.join(directory, target))
                    if not os.path.exists(resolved):
                        missing.append(
                            "{} -> {}".format(os.path.relpath(source_path, ROOT), target)
                        )
        self.assertEqual(missing, [])

    def test_readme_screenshot_is_web_ready_png(self):
        path = os.path.join(ROOT, "docs", "images", "icon-grid-overview.png")
        with open(path, "rb") as handle:
            signature = handle.read(8)
            length = struct.unpack(">I", handle.read(4))[0]
            chunk_type = handle.read(4)
            width, height = struct.unpack(">II", handle.read(8))
        self.assertEqual(signature, b"\x89PNG\r\n\x1a\n")
        self.assertEqual(length, 13)
        self.assertEqual(chunk_type, b"IHDR")
        self.assertEqual(width, 1800)
        self.assertEqual(height, 1170)

    def test_parameter_guide_explains_every_supported_setting(self):
        path = os.path.join(ROOT, "docs", "PARAMETERS.md")
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("Most users need **no IconGrid custom parameter**", source)
        rows = re.findall(
            r"\| `(IconGrid\.[A-Za-z]+)` \| ([^|\n]+) \| ([^|\n]+) \| ([^|\n]+) \|",
            source,
        )
        descriptions = {name: description.strip() for name, description, _accepted, _default in rows}
        self.assertEqual(
            set(descriptions),
            {
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
            },
        )
        self.assertIn("when `gridSize` is unset", descriptions["IconGrid.columns"])
        self.assertIn("when `gridSize` is unset", descriptions["IconGrid.rows"])
        self.assertIn("when `gridSize` is unset", descriptions["IconGrid.rings"])
        self.assertIn("replaces the automatic metric fit", descriptions["IconGrid.padding"])
        self.assertTrue(all(len(description) >= 20 for description in descriptions.values()))

    def test_all_public_screenshots_have_documented_dimensions(self):
        expected = {
            "icon-grid-overview.png": (1800, 1170),
            "show-icon-grid-menu.png": (1200, 800),
            "font-info-grid-size.png": (1200, 800),
            "regular-bold-grid.png": (1600, 900),
            "default-metrics.png": (1530, 424),
            "odd-grid.png": (1600, 1026),
            "even-grid.png": (1600, 1026),
            "glyphs-mcp-edit-profile-1.4.png": (828, 740),
        }
        for filename, dimensions in expected.items():
            path = os.path.join(ROOT, "docs", "images", filename)
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(8), b"\x89PNG\r\n\x1a\n")
                handle.read(8)
                width, height = struct.unpack(">II", handle.read(8))
            with self.subTest(filename=filename):
                self.assertEqual((width, height), dimensions)

    def test_site_build_has_accessible_images_and_no_stale_skill_path(self):
        output = build_site.main()
        index = os.path.join(output, "index.html")
        with open(index, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn('id="install"', source)
        self.assertIn('id="configure"', source)
        self.assertIn('id="mcp"', source)
        self.assertIn("Regular · 84", source)
        self.assertIn("Bold · 135", source)
        self.assertIn("875 units at the default cap height", source)
        self.assertIn("span exactly from baseline to cap height", source)
        self.assertEqual(source.count('href="https://ap.cx"'), 2)
        self.assertIn('href="https://ap.cx/tools/glyphs-mcp"', source)
        self.assertIn(
            'href="https://github.com/thierryc/Glyphs-mcp"',
            source,
        )
        self.assertIn("Copy this request into your AI app", source)
        self.assertIn("This is a read-only check", source)
        self.assertIn("Explain where each value comes from.", source)
        self.assertGreaterEqual(
            source.count("Install GlyphsIconGrid Skill.command"),
            4,
        )
        self.assertNotIn("python3 scripts/install_skill.py", source)
        self.assertNotIn("~/.codex/skills", source)
        self.assertIn("assets/images/odd-grid.png", source)
        self.assertIn("assets/images/even-grid.png", source)
        self.assertNotIn("assets/images/odd-even-grid.png", source)
        image_tags = re.findall(r"<img\s+[^>]*>", source)
        self.assertEqual(len(image_tags), 6)
        for tag in image_tags:
            self.assertRegex(tag, r'alt="[^"]+"')
            source_path = re.search(r'src="([^"]+)"', tag).group(1)
            self.assertTrue(os.path.isfile(os.path.join(output, source_path)))
        output_images = os.path.join(output, "assets", "images")
        self.assertEqual(
            set(os.listdir(output_images)),
            set(build_site.REQUIRED_IMAGES),
        )

    def test_site_source_images_resolve_without_generated_assets(self):
        index = os.path.join(ROOT, "site", "index.html")
        with open(index, "r", encoding="utf-8") as handle:
            source = handle.read()
        image_sources = re.findall(r'<img\s+[^>]*src="([^"]+)"', source)
        self.assertEqual(len(image_sources), len(build_site.REQUIRED_IMAGES))
        for source_path in image_sources:
            self.assertTrue(source_path.startswith("../docs/images/"))
            self.assertTrue(
                os.path.isfile(os.path.normpath(os.path.join(os.path.dirname(index), source_path)))
            )

    def test_site_screenshots_preserve_their_intrinsic_aspect_ratio(self):
        stylesheet = os.path.join(ROOT, "site", "styles.css")
        with open(stylesheet, "r", encoding="utf-8") as handle:
            source = handle.read()
        rule = re.search(r"\.shot-card img\s*\{([^}]+)\}", source).group(1)
        declarations = dict(
            declaration.strip().split(":", 1)
            for declaration in rule.split(";")
            if ":" in declaration
        )
        self.assertEqual(declarations["width"].strip(), "auto")
        self.assertEqual(declarations["max-width"].strip(), "100%")
        self.assertEqual(declarations["height"].strip(), "auto")

        mcp_rule = re.search(r"\.mcp-status-shot img\s*\{([^}]+)\}", source).group(1)
        self.assertIn("padding: clamp(14px, 2.4vw, 24px)", mcp_rule)

    def test_site_uses_apcx_page_tokens_and_semantic_key_values(self):
        stylesheet = os.path.join(ROOT, "site", "styles.css")
        with open(stylesheet, "r", encoding="utf-8") as handle:
            styles = handle.read()
        self.assertIn("--surface: #ffffff", styles)
        self.assertIn("--surface-2: #f7f7f8", styles)
        self.assertIn("--text: #111114", styles)
        self.assertIn("--muted: #5b5b66", styles)
        self.assertIn("--content-max: clamp(960px, 94vw, 1440px)", styles)
        self.assertIn("--content-pad: clamp(16px, 2.4vw, 42px)", styles)
        self.assertIn("--radius: 12px", styles)
        self.assertIn("font-size: clamp(2.2rem, 4.8vw, 3.8rem)", styles)
        self.assertIn("font-size: 0.74rem", styles)
        self.assertIn("font-size: 0.95rem", styles)

        index = os.path.join(ROOT, "site", "index.html")
        with open(index, "r", encoding="utf-8") as handle:
            html = handle.read()
        self.assertRegex(
            html,
            re.compile(r'<dl class="hero-meta"[^>]*>.*?<dt>License</dt>', re.S),
        )
        self.assertRegex(
            html,
            re.compile(
                r'<dl class="master-values"[^>]*>.*?<dt>Regular</dt>.*?<dd><strong>84</strong>',
                re.S,
            ),
        )


if __name__ == "__main__":
    unittest.main()
