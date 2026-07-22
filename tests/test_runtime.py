from __future__ import absolute_import

import unittest

from tests import support  # noqa: F401
from icon_grid.runtime import (
    parameter_entries,
    resolve_layer_context,
    resolve_mouse_context,
    tool_allows_drawing,
)


class Parameter(object):
    def __init__(self, name, value, active=True):
        self.name = name
        self.value = value
        self.active = active


class Owner(object):
    def __init__(self, parameters=None):
        self.customParameters = parameters or []


class RuntimeTests(unittest.TestCase):
    def test_parameter_entries_are_plain_data(self):
        entries = parameter_entries(
            Owner([
                Parameter("IconGrid.columns", 24),
                Parameter("Other", 1),
                Parameter("IconGrid.rows", 30, False),
            ])
        )
        self.assertEqual(
            entries,
            [
                {"name": "IconGrid.columns", "value": 24, "active": True},
                {"name": "IconGrid.rows", "value": 30, "active": False},
            ],
        )

    def test_layer_context_is_safe_for_missing_objects(self):
        self.assertIsNone(resolve_layer_context(None))
        self.assertIsNone(resolve_layer_context(object()))

    def test_layer_context_supports_glyphs_3_and_4_duck_types(self):
        font = Owner()
        master = Owner()
        master.capHeight = 700
        glyph = type("Glyph", (), {"parent": font})()
        layer = type("Layer", (), {"parent": glyph, "master": master, "width": 900})()
        context = resolve_layer_context(layer)
        self.assertEqual(context.width, 900.0)
        self.assertIs(context.font, font)
        self.assertIs(context.master, master)

    def test_text_and_hand_tools_are_suppressed(self):
        class Tool(object):
            def __init__(self, kind):
                self.kind = kind

            def isKindOfClass_(self, value):
                return self.kind == value

        class Controller(object):
            def __init__(self, tool):
                self.tool = tool

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolDrawDelegate(self):
                return self.tool

        lookup = lambda name: name
        self.assertFalse(tool_allows_drawing(Controller(Tool("GlyphsToolText")), lookup))
        self.assertFalse(tool_allows_drawing(Controller(Tool("GlyphsToolHand")), lookup))
        self.assertTrue(tool_allows_drawing(Controller(Tool("GlyphsToolSelect")), lookup))
        self.assertTrue(tool_allows_drawing(None, lookup))

    def test_mouse_context_converts_event_to_active_layer_coordinates(self):
        window = object()
        layer = object()

        class Event(object):
            def window(self):
                return window

        class GraphicView(object):
            def window(self):
                return window

            def activeLayer(self):
                return layer

            def getActiveLocation_(self, event):
                self.event = event
                return type("Point", (), {"x": 12.5, "y": -30.0})()

            def scale(self):
                return 2.0

        graphic_view = GraphicView()
        controller = type("Controller", (), {"graphicView": lambda self: graphic_view})()
        event = Event()
        context = resolve_mouse_context(controller, event)
        self.assertIs(context.layer, layer)
        self.assertEqual(context.point, (12.5, -30.0))
        self.assertEqual(context.scale, 2.0)
        self.assertIs(graphic_view.event, event)

    def test_mouse_context_rejects_other_windows_and_invalid_values(self):
        class GraphicView(object):
            def window(self):
                return object()

            def activeLayer(self):
                return object()

            def getActiveLocation_(self, _event):
                return (math.nan, 0)

            def scale(self):
                return 0

        controller = type("Controller", (), {"graphicView": lambda self: GraphicView()})()
        event = type("Event", (), {"window": lambda self: object()})()
        self.assertIsNone(resolve_mouse_context(controller, event))
        self.assertIsNone(resolve_mouse_context(None, event))
        self.assertIsNone(resolve_mouse_context(controller, None))

    def test_mouse_context_supports_property_shaped_glyphs_api(self):
        window = object()
        layer = object()

        class GraphicView(object):
            def __init__(self):
                self.window = window
                self.activeLayer = layer
                self.scale = 4.0

            def getActiveLocation_(self, _event):
                return (25.0, 75.0)

        controller = type("Controller", (), {})()
        controller.graphicView = GraphicView()
        event = type("Event", (), {})()
        event.window = window
        context = resolve_mouse_context(controller, event)
        self.assertEqual(context.point, (25.0, 75.0))
        self.assertEqual(context.scale, 4.0)
        self.assertIs(context.layer, layer)


if __name__ == "__main__":
    unittest.main()
