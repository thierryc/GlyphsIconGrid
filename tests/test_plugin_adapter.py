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
        self.callbacks = []
        self.redraw_count = 0

    def localize(self, values):
        return values["en"]

    def addCallback(self, callback, operation):
        entry = (callback, operation)
        if entry not in self.callbacks:
            self.callbacks.append(entry)

    def removeCallback(self, callback, operation=None):
        self.callbacks = [
            entry
            for entry in self.callbacks
            if not (
                entry[0] == callback
                and (operation is None or entry[1] == operation)
            )
        ]

    def redraw(self):
        self.redraw_count += 1


FAKE_GLYPHS = FakeGlyphsApplication()


class FakeReporterPlugin(object):
    def __init__(self):
        self.controller = None
        self.messages = []
        self.scale = 2.0

    def getScale(self):
        return self.scale

    def logToConsole(self, message):
        self.messages.append(message)


class Parameter(object):
    def __init__(self, name, value, active=True):
        self.name = name
        self.value = value
        self.active = active


class FakeGraphicView(object):
    def __init__(self, layer):
        self.layer = layer

    def activeLayer(self):
        return self.layer

    def getActiveLocation_(self, event):
        return event.point


class FakeController(object):
    def __init__(self, draw_tool, event_tool, layer):
        self.draw_tool = draw_tool
        self.event_tool = event_tool
        self.graphic_view = FakeGraphicView(layer)

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

    def graphicView(self):
        return self.graphic_view


class FakeMouseEvent(object):
    def __init__(self, point):
        self.point = point


class FakeNotification(object):
    def __init__(self, point):
        self.event = FakeMouseEvent(point)

    def object(self):
        return self.event


class FakeTool(object):
    def __init__(self, class_name, dragging=False, drag_start=(0.0, 0.0), group_id=None):
        self.class_name = class_name
        self.dragging = dragging
        self.dragStart = drag_start
        self.currentTool = None
        self.kvc_values = {}
        self.groupID = group_id if group_id is not None else {
            "GlyphsToolSelect": 10,
            "GlyphsToolText": 20,
            "GlyphsToolDraw": 30,
            "PenTool": 30,
            "GlyphsToolPrimitives": 50,
            "GlyphsToolPrimitivesRect": 50,
            "GlyphsToolPrimitivesCircle": 50,
            "AnnotationTool": 50,
            "GlyphsToolHand": 70,
            "GlyphsToolZoom": 70,
        }.get(class_name, 10)

    def isKindOfClass_(self, class_name):
        if self.class_name == class_name:
            return True
        return (
            self.class_name in ("GlyphsToolPrimitivesRect", "GlyphsToolPrimitivesCircle")
            and class_name == "GlyphsToolPrimitives"
        )

    def className(self):
        return self.class_name

    def valueForKey_(self, key):
        if key not in self.kvc_values:
            raise KeyError(key)
        return self.kvc_values[key]


class FakeDragPoints(object):
    def __init__(self, points=None):
        self.points = list(points or [])

    def count(self):
        return len(self.points)

    def lastPoint(self):
        return self.points[-1]


class FakeNode(object):
    def __init__(self, point):
        self.position = point

    def isKindOfClass_(self, class_name):
        return class_name == "GSNode"


class FakeAnchor(object):
    def __init__(self, point):
        self.position = point

    def isKindOfClass_(self, class_name):
        return class_name == "GSAnchor"


class FreshNodeProxy(object):
    """Model fresh PyObjC wrappers for one retained native GSNode."""

    def __init__(self, token, state):
        self.token = token
        self.state = state

    @property
    def position(self):
        return self.state["position"]

    def isKindOfClass_(self, class_name):
        return class_name == "GSNode"

    def __hash__(self):
        return hash(self.token)

    def __eq__(self, other):
        return isinstance(other, FreshNodeProxy) and self.token == other.token


def owner(**values):
    result = type("Owner", (), {})()
    result.customParameters = [Parameter(name, value) for name, value in values.items()]
    return result


def layer_fixture(font_parameters=None, master_parameters=None, width=1000, selection=None):
    font = owner(**(font_parameters or {}))
    font.upm = 1000
    master = owner(**(master_parameters or {}))
    master.ascender = 800
    master.capHeight = 700
    master.xHeight = 500
    master.descender = -200
    glyph = type("Glyph", (), {"parent": font})()
    return type(
        "Layer",
        (),
        {
            "parent": glyph,
            "master": master,
            "width": width,
            "selection": list(selection or []),
        },
    )()


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
        FAKE_GLYPHS.callbacks = []
        FAKE_GLYPHS.redraw_count = 0
        self.plugin = self.module.GlyphsIconGridReporter()
        self.plugin.settings()

    def configure_tool(
        self,
        layer,
        dragging=False,
        class_name="GlyphsToolSelect",
        scale=2.0,
        controller_as_method=False,
        draw_class_name=None,
    ):
        self.plugin.scale = scale
        event_tool = FakeTool(class_name, dragging)
        draw_tool = FakeTool(draw_class_name or class_name, False)
        controller = FakeController(draw_tool, event_tool, layer)
        self.plugin.controller = (lambda: controller) if controller_as_method else controller
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
        self.assertTrue(
            all(value == (10.0 / 255.0, 132.0 / 255.0, 1.0) for value, _alpha in FakeColor.set_values)
        )

    def test_invalid_parameters_warn_once_across_redraws(self):
        layer = layer_fixture(font_parameters={"IconGrid.columns": "invalid"})
        self.plugin.background(layer)
        self.plugin.background(layer)
        matching = [message for message in self.plugin.messages if "IconGrid.columns" in message]
        self.assertEqual(len(matching), 1)

    def test_master_grid_size_reaches_the_rendered_geometry(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.gridSize": 40,
                "IconGrid.gridMode": "even",
            },
            master_parameters={
                "IconGrid.gridSize": 72,
                "IconGrid.gridMode": "odd",
            },
        )
        config, geometry = self.plugin._geometry_for_layer(layer)
        self.assertEqual(config.grid_size, 72.0)
        self.assertEqual(config.grid_mode, "odd")
        self.assertEqual(geometry.axis_lines, [])
        self.assertTrue(all(ring.radius % 72.0 == 0 for ring in geometry.rings))

    def test_missing_layer_is_safe_noop(self):
        self.assertIsNone(self.plugin.background(None))
        self.assertEqual(FakePath.instances, [])

    def test_creation_hover_callback_lifecycle_is_idempotent(self):
        self.plugin.willActivate()
        self.plugin.willActivate()
        self.assertEqual(len(FAKE_GLYPHS.callbacks), 1)
        self.assertEqual(FAKE_GLYPHS.callbacks[0][1], "mouseMovedNotification")

        self.plugin._creation_hover_layer = object()
        self.plugin._creation_hover_point = (100.0, 200.0)
        self.plugin.willDeactivate()
        self.assertEqual(FAKE_GLYPHS.callbacks, [])
        self.assertIsNone(self.plugin._creation_hover_layer)
        self.assertIsNone(self.plugin._creation_hover_point)

    def test_draw_rectangle_and_circle_hover_while_idle(self):
        for class_name in (
            "GlyphsToolDraw",
            "GlyphsToolPrimitives",
            "GlyphsToolPrimitivesRect",
            "GlyphsToolPrimitivesCircle",
        ):
            with self.subTest(class_name=class_name):
                self.setUp()
                layer = layer_fixture(
                    font_parameters={
                        "IconGrid.columns": 10,
                        "IconGrid.rows": 10,
                        "IconGrid.rings": 0,
                        "IconGrid.spokes": 0,
                        "IconGrid.showKeylines": False,
                        "IconGrid.origin": "bottom-left",
                    }
                )
                self.configure_tool(layer, dragging=False, class_name=class_name)
                self.plugin.willActivate()
                self.plugin._mouse_moved(FakeNotification((200.9, 237.3)))
                self.assertEqual(FAKE_GLYPHS.redraw_count, 1)
                self.plugin._mouse_moved(FakeNotification((200.9, 237.3)))
                self.assertEqual(FAKE_GLYPHS.redraw_count, 1)

                self.plugin.background(layer)
                self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

                self.plugin._mouse_moved(FakeNotification((201.1, 237.3)))
                FakePath.instances = []
                self.plugin.background(layer)
                self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_creation_hover_never_changes_edit_node_behavior(self):
        node = FakeNode((250.0, 237.3))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[node],
        )
        controller = self.configure_tool(
            layer,
            dragging=False,
            class_name="GlyphsToolDraw",
        )
        self.plugin.willActivate()
        self.plugin._mouse_moved(FakeNotification((200.0, 237.3)))
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

        controller.event_tool = FakeTool("GlyphsToolSelect", False)
        controller.draw_tool = controller.event_tool
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

        node.position = (200.0, 237.3)
        controller.event_tool.dragging = True
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_active_shape_endpoint_wins_over_cached_idle_hover(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            }
        )
        controller = self.configure_tool(
            layer,
            dragging=False,
            class_name="GlyphsToolPrimitivesRect",
        )
        self.plugin.willActivate()
        self.plugin._mouse_moved(FakeNotification((200.9, 237.3)))

        controller.event_tool.dragging = True
        controller.event_tool.kvc_values["selectionDrag"] = (201.1, 237.3)
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))
        self.assertIsNone(self.plugin._creation_hover_point)

        controller.event_tool.dragging = False
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_pencil_annotation_and_other_layers_ignore_creation_hover(self):
        for class_name in ("PenTool", "AnnotationTool", "GlyphsToolSelect"):
            with self.subTest(class_name=class_name):
                self.setUp()
                layer = layer_fixture()
                self.configure_tool(layer, dragging=False, class_name=class_name)
                self.plugin.willActivate()
                self.plugin._mouse_moved(FakeNotification((200.0, 237.3)))
                self.plugin.background(layer)
                self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

        self.setUp()
        active_layer = layer_fixture()
        other_layer = layer_fixture()
        self.configure_tool(
            active_layer,
            dragging=False,
            class_name="GlyphsToolDraw",
        )
        self.plugin.willActivate()
        self.plugin._mouse_moved(FakeNotification((200.0, 237.3)))
        self.plugin.background(other_layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_dragging_selected_node_highlights_guides_last_at_constant_screen_width(self):
        node = FakeNode((850.0, 500.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.padding": 1,
                "IconGrid.rings": 4,
                "IconGrid.spokes": 0,
                "IconGrid.origin": "bottom-left",
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        FakePath.instances = []
        FakeColor.set_values = []

        node.position = (900.0, 500.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)

        highlighted = FakePath.instances[-1]
        self.assertTrue(highlighted.stroked)
        self.assertEqual(highlighted.width, 0.7)
        self.assertTrue(any(operation[0] == "oval" for operation in highlighted.operations))
        self.assertTrue(any(operation[0] == "rect" for operation in highlighted.operations))
        self.assertAlmostEqual(FakeColor.set_values[-1][1], 0.448)

    def test_draw_tool_uses_newly_selected_node_for_alignment(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[],
        )
        controller = self.configure_tool(layer, dragging=False, class_name="GlyphsToolDraw")
        self.plugin.background(layer)
        FakePath.instances = []

        layer.selection.append(FakeNode((200.0, 200.0)))
        controller.event_tool.dragging = True
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_draw_tool_uses_live_drag_point_before_a_node_is_selected(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[],
        )
        controller = self.configure_tool(
            layer,
            dragging=True,
            class_name="GlyphsToolDraw",
        )
        controller.event_tool.dragStart = (250.0, 237.3)
        controller.event_tool.kvc_values["dragCurrent"] = (200.9, 237.3)
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_rectangle_and_circle_use_only_the_active_native_drag_endpoint(self):
        for class_name in ("GlyphsToolPrimitivesRect", "GlyphsToolPrimitivesCircle"):
            self.setUp()
            layer = layer_fixture(
                font_parameters={
                    "IconGrid.columns": 10,
                    "IconGrid.rows": 10,
                    "IconGrid.rings": 0,
                    "IconGrid.spokes": 0,
                    "IconGrid.showKeylines": False,
                    "IconGrid.origin": "bottom-left",
                },
                selection=[],
            )
            controller = self.configure_tool(layer, dragging=False, class_name=class_name)
            controller.event_tool.dragStart = (250.0, 237.3)
            controller.event_tool.kvc_values["selectionDrag"] = (200.9, 237.3)

            self.plugin.background(layer)
            self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

            controller.event_tool.dragging = True
            controller.event_tool.kvc_values["selectionDrag"] = (201.1, 237.3)
            FakePath.instances = []
            self.plugin.background(layer)
            self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

            controller.event_tool.kvc_values["selectionDrag"] = (200.9, 237.3)
            FakePath.instances = []
            self.plugin.background(layer)
            self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_pencil_uses_live_stroke_points_and_clears_after_mouse_up(self):
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            },
            selection=[],
        )
        controller = self.configure_tool(layer, dragging=False, class_name="PenTool")
        drag_points = FakeDragPoints([(200.9, 237.3)])
        controller.event_tool.kvc_values["dragPoints"] = drag_points

        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

        drag_points.points.append((200.9, 237.3))
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

        drag_points.points = []
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_annotation_drag_keeps_grid_but_never_highlights(self):
        node = FakeNode((250.0, 237.3))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False, class_name="AnnotationTool")
        self.plugin.background(layer)

        node.position = (200.0, 237.3)
        controller.event_tool.dragging = True
        controller.event_tool.kvc_values["selectionDrag"] = (200.0, 237.3)
        FakePath.instances = []
        self.plugin.background(layer)

        self.assertTrue(any(path.stroked for path in FakePath.instances))
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_selected_node_without_active_drag_does_not_highlight(self):
        layer = layer_fixture(selection=[FakeNode((0.0, 100.0))])
        self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_lasso_drag_with_static_selected_nodes_does_not_highlight(self):
        node = FakeNode((0.0, 100.0))
        layer = layer_fixture(selection=[node])
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        FakePath.instances = []

        controller.event_tool.dragging = True
        self.plugin.background(layer)
        layer.selection.append(FakeNode((100.0, 100.0)))
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_only_nodes_that_move_can_highlight_a_guide(self):
        moving = FakeNode((250.0, 250.0))
        stationary = FakeNode((400.0, 250.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[moving, stationary],
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        FakePath.instances = []

        moving.position = (200.0, 250.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)

        highlighted = [path for path in FakePath.instances if path.width == 0.7][-1]
        highlighted_points = [point for operation, point in highlighted.operations if operation != "rect"]
        self.assertTrue(any(point[0] == 200.0 for point in highlighted_points))
        self.assertFalse(any(point[0] == 400.0 for point in highlighted_points))

    def test_dragging_without_selected_node_ignores_cursor_and_non_nodes(self):
        for selection in ([], [FakeAnchor((0.0, 100.0))]):
            FakePath.instances = []
            layer = layer_fixture(selection=selection)
            self.configure_tool(layer, dragging=True)
            self.plugin.background(layer)
            self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_alignment_highlight_can_be_disabled_by_custom_parameter(self):
        node = FakeNode((50.0, 100.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.alignmentHighlight": False,
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        FakePath.instances = []

        node.position = (0.0, 100.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

    def test_callable_controller_shape_supports_drag_alignment(self):
        node = FakeNode((250.0, 200.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.width": 1000,
                "IconGrid.height": 1000,
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False, controller_as_method=True)
        self.plugin.background(layer)
        FakePath.instances = []

        node.position = (200.0, 200.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_active_event_tool_controls_temporary_drag_state(self):
        node = FakeNode((250.0, 200.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            },
            selection=[node],
        )
        controller = self.configure_tool(
            layer,
            dragging=False,
            class_name="GlyphsToolSelect",
            draw_class_name="GlyphsToolDraw",
        )
        self.plugin.background(layer)
        FakePath.instances = []

        node.position = (200.0, 200.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_native_node_identity_survives_fresh_python_proxies(self):
        state = {"position": (250.0, 200.0)}
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
            },
        )
        layer.__class__.selection = property(
            lambda _layer: [FreshNodeProxy("native-node-1", state)]
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)
        FakePath.instances = []

        state["position"] = (200.0, 200.0)
        controller.event_tool.dragging = True
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_new_drag_session_resets_prior_alignment_without_mouseup_draw(self):
        node = FakeNode((250.0, 200.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)

        node.position = (200.0, 200.0)
        controller.event_tool.dragging = True
        controller.event_tool.dragStart = (250.0, 200.0)
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

        controller.event_tool.dragStart = (200.0, 200.0)
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

        node.position = (100.0, 200.0)
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

    def test_default_alignment_tolerance_is_strict_and_scale_independent(self):
        node = FakeNode((250.0, 250.0))
        layer = layer_fixture(
            font_parameters={
                "IconGrid.columns": 10,
                "IconGrid.rows": 10,
                "IconGrid.rings": 0,
                "IconGrid.spokes": 0,
                "IconGrid.showKeylines": False,
                "IconGrid.origin": "bottom-left",
                "IconGrid.gridMode": "even",
            },
            selection=[node],
        )
        controller = self.configure_tool(layer, dragging=False)
        self.plugin.background(layer)

        node.position = (201.1, 250.0)
        controller.event_tool.dragging = True
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 0.7 for path in FakePath.instances))

        node.position = (200.9, 250.0)
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 0.7 for path in FakePath.instances))

        controller.event_tool.dragging = False
        node.position = (250.0, 250.0)
        self.plugin.scale = 1.0
        self.plugin.background(layer)

        node.position = (202.1, 250.0)
        controller.event_tool.dragging = True
        controller.event_tool.dragStart = (250.0, 250.0)
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertFalse(any(path.width == 1.4 for path in FakePath.instances))

        node.position = (201.9, 250.0)
        FakePath.instances = []
        self.plugin.background(layer)
        self.assertTrue(any(path.width == 1.4 for path in FakePath.instances))

    def test_hand_tool_suppresses_grid_and_alignment(self):
        layer = layer_fixture(selection=[FakeNode((0.0, 100.0))])
        self.configure_tool(layer, dragging=True, class_name="GlyphsToolHand")
        self.plugin.background(layer)
        self.assertEqual(FakePath.instances, [])


if __name__ == "__main__":
    unittest.main()
