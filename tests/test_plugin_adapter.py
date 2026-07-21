from __future__ import absolute_import

import importlib.util
import os
import sys
import types
import unittest

from tests import support


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_PATH = os.path.join(
    ROOT, "IconGrid.glyphsReporter", "Contents", "Resources", "plugin.py"
)


class FakePath(object):
    instances = []

    def __init__(self):
        self.operations = []
        self.width = None
        self.stroked = False
        self.__class__.instances.append(self)

    @classmethod
    def bezierPath(cls):
        return cls()

    def moveToPoint_(self, point):
        self.operations.append(("move", point))

    def lineToPoint_(self, point):
        self.operations.append(("line", point))

    def appendBezierPathWithRect_(self, rect):
        self.operations.append(("rect", rect))

    def appendBezierPathWithOvalInRect_(self, rect):
        self.operations.append(("oval", rect))

    def setLineWidth_(self, width):
        self.width = width

    def stroke(self):
        self.stroked = True


class FakeColor(object):
    def __init__(self, value="semantic", alpha=1.0):
        self.value = value
        self.alpha = alpha

    @classmethod
    def controlAccentColor(cls):
        return cls()

    @classmethod
    def gridColor(cls):
        return cls("grid")

    @classmethod
    def colorWithCalibratedRed_green_blue_alpha_(cls, red, green, blue, alpha):
        return cls((red, green, blue), alpha)

    def colorWithAlphaComponent_(self, alpha):
        return self.__class__(self.value, alpha)

    def set(self):
        return None


class FakeReporterPlugin(object):
    def __init__(self):
        self.controller = None
        self.messages = []

    def getScale(self):
        return 2.0

    def logToConsole(self, message):
        self.messages.append(message)


class Parameter(object):
    def __init__(self, name, value, active=True):
        self.name = name
        self.value = value
        self.active = active


def owner(**values):
    result = type("Owner", (), {})()
    result.customParameters = [Parameter(name, value) for name, value in values.items()]
    return result


def layer_fixture(font_parameters=None, master_parameters=None, width=1000):
    font = owner(**(font_parameters or {}))
    font.upm = 1000
    master = owner(**(master_parameters or {}))
    master.capHeight = 700
    glyph = type("Glyph", (), {"parent": font})()
    return type("Layer", (), {"parent": glyph, "master": master, "width": width})()


class PluginAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original_modules = {
            name: sys.modules.get(name)
            for name in ("objc", "AppKit", "GlyphsApp", "GlyphsApp.plugins")
        }
        objc = types.ModuleType("objc")
        objc.python_method = lambda function: function
        appkit = types.ModuleType("AppKit")
        appkit.NSBezierPath = FakePath
        appkit.NSColor = FakeColor
        appkit.NSMakeRect = lambda x, y, width, height: (x, y, width, height)
        appkit.NSClassFromString = lambda _name: None
        glyphs = types.ModuleType("GlyphsApp")
        glyphs.Glyphs = type("Glyphs", (), {"localize": staticmethod(lambda values: values["en"])})()
        plugins = types.ModuleType("GlyphsApp.plugins")
        plugins.ReporterPlugin = FakeReporterPlugin
        sys.modules.update({
            "objc": objc,
            "AppKit": appkit,
            "GlyphsApp": glyphs,
            "GlyphsApp.plugins": plugins,
        })
        spec = importlib.util.spec_from_file_location("icon_grid_test_plugin", PLUGIN_PATH)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    @classmethod
    def tearDownClass(cls):
        sys.modules.pop("icon_grid_test_plugin", None)
        for name, module in cls.original_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module

    def setUp(self):
        FakePath.instances = []
        self.plugin = self.module.GlyphsIconGrid()
        self.plugin.settings()

    def test_menu_has_no_additional_ui(self):
        self.assertEqual(self.plugin.menuName, "Icon Grid")
        self.assertFalse(hasattr(self.plugin, "generalContextMenus"))

    def test_background_batches_and_strokes_geometry(self):
        self.plugin.background(layer_fixture())
        stroked = [path for path in FakePath.instances if path.stroked]
        self.assertGreaterEqual(len(stroked), 4)
        self.assertTrue(all(path.width > 0 for path in stroked))
        self.assertTrue(any(operation[0] == "oval" for path in stroked for operation in path.operations))

    def test_invalid_parameters_warn_once_across_redraws(self):
        layer = layer_fixture(font_parameters={"IconGrid.columns": "invalid"})
        self.plugin.background(layer)
        self.plugin.background(layer)
        matching = [message for message in self.plugin.messages if "IconGrid.columns" in message]
        self.assertEqual(len(matching), 1)

    def test_missing_layer_is_safe_noop(self):
        self.assertIsNone(self.plugin.background(None))
        self.assertEqual(FakePath.instances, [])


if __name__ == "__main__":
    unittest.main()
