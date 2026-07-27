from __future__ import absolute_import

import ast
import os
import plistlib
import subprocess
import struct
import sys
import tempfile
import unittest
import zipfile

from scripts import package as package_script


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.path.join(ROOT, "IconGrid.glyphsReporter")
RESOURCES = os.path.join(BUNDLE, "Contents", "Resources")


class BundleTests(unittest.TestCase):
    def test_bundle_identity_and_principal_class(self):
        with open(os.path.join(BUNDLE, "Contents", "Info.plist"), "rb") as handle:
            info = plistlib.load(handle)
        self.assertEqual(info["CFBundleIdentifier"], "com.thierryc.GlyphsIconGrid")
        self.assertEqual(info["CFBundleName"], "IconGrid")
        self.assertEqual(info["NSPrincipalClass"], "GlyphsIconGridReporter")
        self.assertEqual(info["CFBundleShortVersionString"], "0.1.0")
        self.assertEqual(info["CFBundleVersion"], "1")
        self.assertEqual(
            info["productPageURL"], "https://thierryc.github.io/GlyphsIconGrid/"
        )

    def test_all_python_sources_parse(self):
        for directory, _subdirectories, files in os.walk(RESOURCES):
            for filename in files:
                if filename.endswith(".py"):
                    path = os.path.join(directory, filename)
                    with open(path, "r", encoding="utf-8") as handle:
                        ast.parse(handle.read(), filename=path)

    def test_core_modules_do_not_import_glyphs_or_appkit(self):
        for filename in ("config.py", "geometry.py", "runtime.py"):
            path = os.path.join(RESOURCES, "glyphs_icon_grid", filename)
            with open(path, "r", encoding="utf-8") as handle:
                source = handle.read()
            tree = ast.parse(source, filename=path)
            imported_roots = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported_roots.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported_roots.add(node.module.split(".")[0])
            self.assertNotIn("GlyphsApp", imported_roots)
            self.assertNotIn("AppKit", imported_roots)

    def test_sdk_loader_is_executable_and_universal(self):
        loader = os.path.join(BUNDLE, "Contents", "MacOS", "plugin")
        self.assertTrue(os.access(loader, os.X_OK))
        with open(loader, "rb") as handle:
            magic = handle.read(4)
        self.assertIn(struct.unpack(">I", magic)[0], (0xCAFEBABE, 0xCAFEBABF))

    def test_python_entry_point_keeps_official_template_executable_mode(self):
        plugin_source = os.path.join(RESOURCES, "plugin.py")
        self.assertTrue(os.access(plugin_source, os.X_OK))

    def test_tracked_fixture_has_two_masters_and_weight_matched_h_stems(self):
        fixture = os.path.join(ROOT, "tests", "fixtures", "IconGrid-Test.glyphs")
        with open(fixture, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertEqual(source.count("id = regular;"), 1)
        self.assertEqual(source.count("id = bold;"), 1)
        self.assertGreaterEqual(source.count("width = 1000;"), 2)
        self.assertEqual(source.count("name = IconGrid."), 0)
        self.assertEqual(source.count("customParameters = ("), 0)
        self.assertIn('name = "H Horizontal Stem";', source)
        self.assertIn("stemValues = (\n84\n);", source)
        self.assertIn("stemValues = (\n135\n);", source)

    def test_release_archive_includes_bundle_skill_installer_license_and_notice(self):
        output = package_script.main()
        with zipfile.ZipFile(output, "r") as archive:
            names = archive.namelist()
            installer = archive.getinfo("Install GlyphsIconGrid Skill.command")
        self.assertIn("IconGrid.glyphsReporter/Contents/Info.plist", names)
        self.assertIn("skills/glyphs-mcp-icon-grid/SKILL.md", names)
        self.assertIn(
            "skills/glyphs-mcp-icon-grid/references/parameters.md",
            names,
        )
        self.assertEqual((installer.external_attr >> 16) & 0o777, 0o755)
        self.assertIn("LICENSE", names)
        self.assertIn("NOTICE", names)
        self.assertTrue(os.path.isfile(output + ".sha256"))

    def test_macos_skill_installer_is_self_contained_and_python_free(self):
        path = os.path.join(ROOT, "scripts", "Install GlyphsIconGrid Skill.command")
        self.assertTrue(os.access(path, os.X_OK))
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn('SOURCE="${RELEASE_ROOT}/skills/glyphs-mcp-icon-grid"', source)
        self.assertIn("/usr/bin/ditto", source)
        self.assertIn(".agents/skills", source)
        self.assertIn(".claude/skills", source)
        self.assertIn("dated backup", source)
        self.assertNotIn("python3", source)

    @unittest.skipUnless(sys.platform == "darwin", "requires macOS")
    def test_macos_skill_installer_copies_to_shared_user_location(self):
        installer = os.path.join(
            ROOT, "scripts", "Install GlyphsIconGrid Skill.command"
        )
        with tempfile.TemporaryDirectory() as install_home:
            environment = os.environ.copy()
            environment["GLYPHS_ICON_GRID_SKILL_HOME"] = install_home
            result = subprocess.run(
                [installer, "shared"],
                check=False,
                capture_output=True,
                text=True,
                env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            destination = os.path.join(
                install_home, ".agents", "skills", "glyphs-mcp-icon-grid"
            )
            self.assertTrue(os.path.isfile(os.path.join(destination, "SKILL.md")))
            self.assertTrue(
                os.path.isfile(
                    os.path.join(destination, "references", "parameters.md")
                )
            )


if __name__ == "__main__":
    unittest.main()
