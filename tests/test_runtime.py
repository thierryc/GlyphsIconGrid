from __future__ import absolute_import

import unittest

from tests import support  # noqa: F401
from glyphs_icon_grid.runtime import (
    active_mouse_context,
    parameter_entries,
    resolve_layer_context,
    selected_node_records,
    selected_node_points,
    tool_allows_drawing,
    tool_creation_drag_point,
    tool_drag_session,
    tool_is_annotation,
    tool_is_drawing,
    tool_is_dragging,
    tool_is_freehand_drawing,
    tool_is_outline_creation,
    tool_is_shape_drawing,
    tool_uses_creation_hover,
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

    def test_text_hand_and_zoom_tools_are_suppressed_without_group_assumptions(self):
        class Tool(object):
            def __init__(self, kind):
                self.kind = kind

            def isKindOfClass_(self, value):
                return self.kind == value

        class Controller(object):
            def __init__(self, event_tool, draw_tool=None):
                self.event_tool = event_tool
                self.draw_tool = draw_tool or event_tool

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolDrawDelegate(self):
                return self.draw_tool

            def toolEventDelegate(self):
                return self.event_tool

            def toolEventDelegateSelected(self):
                return self.draw_tool

        lookup = lambda name: name
        self.assertFalse(tool_allows_drawing(Controller(Tool("GlyphsToolText")), lookup))
        self.assertFalse(tool_allows_drawing(Controller(Tool("GlyphsToolHand")), lookup))
        self.assertFalse(tool_allows_drawing(Controller(Tool("GlyphsToolZoom")), lookup))
        draw = Tool("GlyphsToolDraw")
        draw.groupID = 30
        self.assertTrue(tool_allows_drawing(Controller(draw), lookup))
        self.assertTrue(tool_allows_drawing(Controller(Tool("GlyphsToolSelect")), lookup))
        self.assertTrue(
            tool_allows_drawing(
                Controller(Tool("GlyphsToolSelect"), Tool("GlyphsToolText")),
                lookup,
            )
        )
        self.assertTrue(tool_allows_drawing(None, lookup))

    def test_tool_dragging_uses_native_tool_state(self):
        class Tool(object):
            def __init__(self, dragging):
                self.dragging = dragging
                self.dragStart = (12, 34)

        class Controller(object):
            def __init__(self, event_tool, draw_tool=None):
                self.event_tool = event_tool
                self.draw_tool = draw_tool or event_tool

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolDrawDelegate(self):
                return self.draw_tool

            def toolEventDelegate(self):
                return self.event_tool

            def toolEventDelegateSelected(self):
                return self.draw_tool

        class LegacyController(object):
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

        class CallableTool(object):
            def dragging(self):
                return True

            def dragStart(self):
                return (56, 78)

        self.assertTrue(tool_is_dragging(Controller(Tool(True))))
        self.assertFalse(tool_is_dragging(Controller(Tool(False))))
        self.assertTrue(tool_is_dragging(Controller(Tool(True), Tool(False))))
        self.assertFalse(tool_is_dragging(Controller(object())))
        self.assertFalse(tool_is_dragging(None))
        session = tool_drag_session(Controller(Tool(True)))
        self.assertEqual(session[1], (12.0, 34.0))
        self.assertIsNone(tool_drag_session(Controller(Tool(False))))
        self.assertTrue(tool_is_dragging(LegacyController(Tool(True))))
        self.assertEqual(tool_drag_session(LegacyController(CallableTool()))[1], (56.0, 78.0))

    def test_drawing_tool_uses_active_event_delegate(self):
        class Tool(object):
            def __init__(self, kind, group_id=None):
                self.kind = kind
                self.groupID = group_id

            def isKindOfClass_(self, value):
                return self.kind == value

        class Controller(object):
            def __init__(self, event_tool, draw_tool):
                self.event_tool = event_tool
                self.draw_tool = draw_tool

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolDrawDelegate(self):
                return self.draw_tool

            def toolEventDelegate(self):
                return self.event_tool

        lookup = lambda name: name
        self.assertTrue(
            tool_is_drawing(
                Controller(Tool("GlyphsToolDraw"), Tool("GlyphsToolSelect")),
                lookup,
            )
        )
        self.assertFalse(
            tool_is_drawing(
                Controller(Tool("GlyphsToolSelect"), Tool("GlyphsToolDraw")),
                lookup,
            )
        )
        self.assertFalse(
            tool_is_drawing(
                Controller(Tool("ThirdPartyPen", 20), Tool("GlyphsToolSelect")),
                lookup,
            )
        )

    def test_outline_creation_tools_and_live_drag_points(self):
        hierarchy = {
            "GlyphsToolPrimitivesRect": {"GlyphsToolPrimitives"},
            "GlyphsToolPrimitivesCircle": {"GlyphsToolPrimitives"},
        }

        class PointBox(object):
            def __init__(self, point):
                self.point = point

            def pointValue(self):
                return self.point

        class DragPoints(object):
            def __init__(self, points):
                self.points = list(points)

            def count(self):
                return len(self.points)

            def lastPoint(self):
                return self.points[-1]

        class Tool(object):
            def __init__(
                self,
                kind,
                dragging=False,
                group_id=10,
                drag_start=(10, 20),
                values=None,
                current_tool=None,
            ):
                self.kind = kind
                self.dragging = dragging
                self.groupID = group_id
                self.dragStart = drag_start
                self.values = values or {}
                self.currentTool = current_tool

            def className(self):
                return self.kind

            def isKindOfClass_(self, value):
                return self.kind == value or value in hierarchy.get(self.kind, set())

            def valueForKey_(self, key):
                if key not in self.values:
                    raise KeyError(key)
                return self.values[key]

        class Controller(object):
            def __init__(self, event_tool, draw_tool=None):
                self.event_tool = event_tool
                self.draw_tool = draw_tool or event_tool

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolDrawDelegate(self):
                return self.draw_tool

            def toolEventDelegate(self):
                return self.event_tool

        lookup = lambda name: name
        for class_name, point_key in (
            ("GlyphsToolPrimitives", "auswahlDrag"),
            ("GlyphsToolPrimitivesRect", "selectionDrag"),
            ("GlyphsToolPrimitivesCircle", "selectionDrag"),
        ):
            tool = Tool(
                class_name,
                dragging=True,
                values={point_key: PointBox((200, 300))},
            )
            controller = Controller(tool)
            self.assertTrue(tool_is_shape_drawing(controller, lookup))
            self.assertTrue(tool_is_outline_creation(controller, lookup))
            self.assertEqual(tool_creation_drag_point(controller, lookup), (200.0, 300.0))

        pen_points = DragPoints([(350, 450), (400, 500)])
        pen = Controller(Tool("PenTool", values={"dragPoints": pen_points}))
        self.assertTrue(tool_is_outline_creation(pen, lookup))
        self.assertTrue(tool_is_freehand_drawing(pen, lookup))
        self.assertFalse(tool_is_shape_drawing(pen, lookup))
        self.assertEqual(tool_creation_drag_point(pen, lookup), (400.0, 500.0))

        pen_points.points = []
        self.assertIsNone(tool_creation_drag_point(pen, lookup))

        passive_shape = Controller(
            Tool("GlyphsToolPrimitivesRect", values={"selectionDrag": (200, 300)})
        )
        self.assertIsNone(tool_creation_drag_point(passive_shape, lookup))

        annotation = Controller(
            Tool(
                "AnnotationTool",
                dragging=True,
                group_id=50,
                values={"selectionDrag": (200, 300)},
            )
        )
        self.assertTrue(tool_is_annotation(annotation, lookup))
        self.assertFalse(tool_is_drawing(annotation, lookup))
        self.assertFalse(tool_is_outline_creation(annotation, lookup))
        self.assertIsNone(tool_creation_drag_point(annotation, lookup))

        circle = Tool(
            "GlyphsToolPrimitivesCircle",
            dragging=True,
            values={"selectionDrag": (600, 700)},
        )
        group = Controller(Tool("GSToolGroup", current_tool=circle, group_id=50))
        self.assertTrue(tool_is_shape_drawing(group, lookup))
        self.assertEqual(tool_creation_drag_point(group, lookup), (600.0, 700.0))

        self.assertTrue(tool_uses_creation_hover(group, lookup))
        self.assertTrue(
            tool_uses_creation_hover(
                Controller(Tool("GlyphsToolDraw")),
                lookup,
            )
        )
        self.assertFalse(tool_uses_creation_hover(pen, lookup))
        self.assertFalse(tool_uses_creation_hover(annotation, lookup))
        self.assertFalse(
            tool_uses_creation_hover(
                Controller(Tool("GlyphsToolSelect")),
                lookup,
            )
        )

    def test_active_mouse_context_uses_edit_view_glyph_coordinates(self):
        layer = object()
        window = object()

        class Event(object):
            def window(self):
                return window

        event = Event()

        class Notification(object):
            def object(self):
                return event

        class GraphicView(object):
            def window(self):
                return window

            def activeLayer(self):
                return layer

            def getActiveLocation_(self, received_event):
                self.received_event = received_event
                return (200.9, 237.3)

        class Controller(object):
            def __init__(self):
                self.graphic_view = GraphicView()

            def graphicView(self):
                return self.graphic_view

        controller = Controller()
        self.assertEqual(
            active_mouse_context(controller, Notification()),
            (layer, (200.9, 237.3)),
        )
        self.assertIs(controller.graphic_view.received_event, event)
        self.assertIsNone(active_mouse_context(controller, None))
        self.assertIsNone(active_mouse_context(object(), Notification()))

        event.window = lambda: object()
        self.assertIsNone(active_mouse_context(controller, Notification()))

    def test_unimplemented_native_optional_selector_is_ignored(self):
        class Tool(object):
            dragging = True

            def className(self):
                return "GlyphsToolPrimitivesRect"

            def isKindOfClass_(self, value):
                return value in (
                    "GlyphsToolPrimitives",
                    "GlyphsToolPrimitivesRect",
                )

            def eventHandler(self):
                raise ValueError("unrecognized selector sent to instance")

            def selectionDrag(self):
                raise ValueError("NSInvalidArgumentException")

            def valueForKey_(self, key):
                if key == "selectionDrag":
                    return (200.9, 237.3)
                raise KeyError(key)

        class Controller(object):
            def __init__(self):
                self.tool = Tool()

            def view(self):
                return self

            def window(self):
                return self

            def windowController(self):
                return self

            def toolEventDelegate(self):
                return self.tool

        controller = Controller()
        lookup = lambda name: name
        self.assertTrue(tool_is_shape_drawing(controller, lookup))
        self.assertEqual(
            tool_creation_drag_point(controller, lookup),
            (200.9, 237.3),
        )

    def test_selected_node_points_ignore_non_nodes_invalid_values_and_duplicates(self):
        class Point(object):
            def __init__(self, x, y):
                self.x = x
                self.y = y

        class Selectable(object):
            def __init__(self, kind, point):
                self.kind = kind
                self.position = point

            def isKindOfClass_(self, value):
                return self.kind == value

        layer = type("Layer", (), {})()
        layer.selection = [
            Selectable("GSNode", Point(100, 200)),
            Selectable("GSAnchor", Point(300, 400)),
            Selectable("GSNode", Point(100, 200)),
            Selectable("GSNode", Point(float("nan"), 0)),
        ]
        self.assertEqual(
            selected_node_points(layer, lambda name: name),
            ((100.0, 200.0),),
        )
        records = selected_node_records(layer, lambda name: name)
        self.assertEqual(len(records), 2)
        self.assertEqual([point for _node, point in records], [(100.0, 200.0)] * 2)

    def test_selected_node_points_support_callable_selection_and_position(self):
        class Node(object):
            def position(self):
                return (25, -75)

        layer = type("Layer", (), {"selection": lambda self: [Node()]})()
        self.assertEqual(selected_node_points(layer, lambda _name: None), ((25.0, -75.0),))
        self.assertEqual(selected_node_points(None, lambda _name: None), ())
        self.assertEqual(selected_node_points(object(), lambda _name: None), ())


if __name__ == "__main__":
    unittest.main()
