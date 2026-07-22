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
    set_values = []

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
        self.__class__.set_values.append((self.value, self.alpha))
        return None


class FakeGlyphsApplication(object):
    def __init__(self):
        self.reset()

    def reset(self):
        self.callbacks = []
        self.removed_callbacks = []
        self.redraw_count = 0
        self.current_event = None

    def localize(self, values):
        return values["en"]

    def addCallback(self, callback, operation):
        self.callbacks.append((callback, operation))

    def removeCallback(self, callback, operation):
        self.removed_callbacks.append((callback, operation))

    def redraw(self):
        self.redraw_count += 1

    def currentEvent(self):
        return self.current_event


FAKE_GLYPHS = FakeGlyphsApplication()


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


class FakeEvent(object):
    def __init__(self, window, point):
        self._window = window
        self.point = point

    def window(self):
        return self._window


class FakeGraphicView(object):
    def __init__(self, window, layer, scale=2.0):
        self._window = window
        self._layer = layer
        self._scale = scale

    def window(self):
        return self._window

    def activeLayer(self):
        return self._layer

    def getActiveLocation_(self, event):
        return event.point

    def scale(self):
        return self._scale


class FakeController(object):
    def __init__(self, layer, scale=2.0, tool=None):
        self._tool = tool
        self._graphic_view = FakeGraphicView(self, layer, scale)

    def graphicView(self):
        return self._graphic_view

    def view(self):
        return self

    def window(self):
        return self

    def windowController(self):
        return self

    def toolDrawDelegate(self):
        return self._tool


class FakeTool(object):
    def __init__(self, class_name):
        self.class_name = class_name

    def isKindOfClass_(self, class_name):
        return self.class_name == class_name


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
        appkit.NSClassFromString = lambda name: name
        glyphs = types.ModuleType("GlyphsApp")
        glyphs.Glyphs = FAKE_GLYPHS
        glyphs.MOUSEMOVED = "mouseMovedNotification"
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
        FakeColor.set_values = []
        FAKE_GLYPHS.reset()
        self.plugin = self.module.GlyphsIconGrid()
        self.plugin.settings()

    def configure_mouse(self, layer, point, scale=2.0):
        controller = FakeController(layer, scale)
        self.plugin.controller = controller
        FAKE_GLYPHS.current_event = FakeEvent(controller, point)
        return controller

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

    def test_mouse_callback_registers_once_and_is_removed_on_deactivation(self):
        self.plugin.willActivate()
        callback = FAKE_GLYPHS.callbacks[0][0]
        self.plugin.willActivate()
        self.assertEqual(FAKE_GLYPHS.callbacks, [(callback, "mouseMovedNotification")])

        self.plugin.willDeactivate()
        self.assertEqual(
            FAKE_GLYPHS.removed_callbacks,
            [(callback, "mouseMovedNotification")],
        )
        self.assertIsNone(self.plugin._mouse_callback)
        self.assertEqual(self.plugin._hover_hits, ())

    def test_mouse_move_redraws_only_when_hovered_guides_change(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
            }
        )
        controller = self.configure_mouse(layer, (0.0, 150.0))
        self.plugin._mouse_moved(None)
        self.assertEqual(FAKE_GLYPHS.redraw_count, 1)
        first_hits = self.plugin._hover_hits
        self.assertTrue(first_hits)

        FAKE_GLYPHS.current_event = FakeEvent(controller, (0.0, 250.0))
        self.plugin._mouse_moved(None)
        self.assertEqual(self.plugin._hover_hits, first_hits)
        self.assertEqual(FAKE_GLYPHS.redraw_count, 1)

        FAKE_GLYPHS.current_event = FakeEvent(controller, (50.0, 50.0))
        self.plugin._mouse_moved(None)
        self.assertEqual(self.plugin._hover_hits, ())
        self.assertEqual(FAKE_GLYPHS.redraw_count, 2)

    def test_hover_strokes_selected_guides_last_at_constant_screen_width(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.padding": 1,
                "IconGrid.rings": 4,
                "IconGrid.spokes": 0,
            }
        )
        self.configure_mouse(layer, (900.0, 500.0), scale=2.0)
        self.plugin._mouse_moved(None)
        self.plugin.background(layer)

        highlighted = FakePath.instances[-1]
        self.assertTrue(highlighted.stroked)
        self.assertEqual(highlighted.width, 1.0)
        self.assertTrue(any(operation[0] == "oval" for operation in highlighted.operations))
        self.assertTrue(any(operation[0] == "rect" for operation in highlighted.operations))
        self.assertAlmostEqual(FakeColor.set_values[-1][1], 0.7)

    def test_hover_can_be_disabled_by_custom_parameter(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.hoverHighlight": False,
            }
        )
        self.configure_mouse(layer, (0.0, 100.0))
        self.plugin._mouse_moved(None)
        self.assertEqual(self.plugin._hover_hits, ())
        self.assertEqual(FAKE_GLYPHS.redraw_count, 0)

        self.plugin.background(layer)
        self.assertFalse(any(path.width == 1.0 for path in FakePath.instances))

    def test_mouse_move_clears_hover_for_missing_or_other_window_events(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
            }
        )
        controller = self.configure_mouse(layer, (0.0, 150.0))
        self.plugin._mouse_moved(None)
        self.assertTrue(self.plugin._hover_hits)

        FAKE_GLYPHS.current_event = FakeEvent(object(), (0.0, 150.0))
        self.plugin._mouse_moved(None)
        self.assertEqual(self.plugin._hover_hits, ())
        self.assertEqual(FAKE_GLYPHS.redraw_count, 2)

        FAKE_GLYPHS.current_event = None
        self.plugin._mouse_moved(None)
        self.assertEqual(FAKE_GLYPHS.redraw_count, 2)
        self.assertIs(self.plugin.controller, controller)

    def test_mouse_move_clears_hover_for_unsupported_tools(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
            }
        )
        controller = self.configure_mouse(layer, (0.0, 150.0))
        self.plugin._mouse_moved(None)
        self.assertTrue(self.plugin._hover_hits)

        controller._tool = FakeTool("GlyphsToolHand")
        self.plugin._mouse_moved(None)
        self.assertEqual(self.plugin._hover_hits, ())
        self.assertEqual(FAKE_GLYPHS.redraw_count, 2)


if __name__ == "__main__":
    unittest.main()
