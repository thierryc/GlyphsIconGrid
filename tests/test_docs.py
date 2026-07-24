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

    def test_all_public_screenshots_have_documented_dimensions(self):
        expected = {
            "icon-grid-overview.png": (1800, 1170),
            "show-icon-grid-menu.png": (1200, 800),
            "font-info-grid-size.png": (1200, 800),
            "regular-bold-grid.png": (1600, 900),
            "odd-even-grid.png": (1600, 900),
            "glyphs-mcp-edit-profile.png": (1200, 800),
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
        self.assertIn("Regular · 34", source)
        self.assertIn("Bold · 72", source)
        self.assertNotIn("~/.codex/skills", source)
        image_tags = re.findall(r"<img\s+[^>]*>", source)
        self.assertEqual(len(image_tags), 6)
        for tag in image_tags:
            self.assertRegex(tag, r'alt="[^"]+"')
            source_path = re.search(r'src="([^"]+)"', tag).group(1)
            self.assertTrue(os.path.isfile(os.path.join(output, source_path)))

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


if __name__ == "__main__":
    unittest.main()
