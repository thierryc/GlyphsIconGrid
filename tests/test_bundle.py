from __future__ import absolute_import

import ast
import os
import plistlib
import struct
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE = os.path.join(ROOT, "IconGrid.glyphsReporter")
RESOURCES = os.path.join(BUNDLE, "Contents", "Resources")


class BundleTests(unittest.TestCase):
    def test_bundle_identity_and_principal_class(self):
        with open(os.path.join(BUNDLE, "Contents", "Info.plist"), "rb") as handle:
            info = plistlib.load(handle)
        self.assertEqual(info["CFBundleIdentifier"], "com.thierryc.GlyphsIconGrid")
        self.assertEqual(info["CFBundleName"], "IconGrid")
        self.assertEqual(info["NSPrincipalClass"], "GlyphsIconGrid")
        self.assertEqual(info["CFBundleShortVersionString"], "0.1.0")

    def test_all_python_sources_parse(self):
        for directory, _subdirectories, files in os.walk(RESOURCES):
            for filename in files:
                if filename.endswith(".py"):
                    path = os.path.join(directory, filename)
                    with open(path, "r", encoding="utf-8") as handle:
                        ast.parse(handle.read(), filename=path)

    def test_core_modules_do_not_import_glyphs_or_appkit(self):
        for filename in ("config.py", "geometry.py", "runtime.py"):
            path = os.path.join(RESOURCES, "icon_grid", filename)
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

    def test_disposable_fixture_has_two_masters_and_two_widths(self):
        fixture = os.path.join(ROOT, "tests", "fixtures", "IconGrid-Test.glyphs")
        with open(fixture, "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertEqual(source.count("id = regular;"), 1)
        self.assertEqual(source.count("id = bold;"), 1)
        self.assertIn("width = 1000;", source)
        self.assertIn("width = 800;", source)


if __name__ == "__main__":
    unittest.main()
