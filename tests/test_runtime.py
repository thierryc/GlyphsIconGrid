from __future__ import absolute_import

import unittest

from tests import support  # noqa: F401
from icon_grid.runtime import parameter_entries, resolve_layer_context, tool_allows_drawing


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


if __name__ == "__main__":
    unittest.main()
