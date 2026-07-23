"""Duck-typed Glyphs runtime adapters, kept importable outside Glyphs."""

from __future__ import absolute_import

import math
from collections import namedtuple


LayerContext = namedtuple("LayerContext", "layer glyph font master width")


def parameter_entries(owner):
    entries = []
    if owner is None:
        return entries
    parameters = getattr(owner, "customParameters", None)
    if parameters is None:
        return entries
    try:
        iterator = iter(parameters)
    except TypeError:
        return entries
    for parameter in iterator:
        name = getattr(parameter, "name", None)
        if not isinstance(name, str) or not name.startswith("IconGrid."):
            continue
        entries.append(
            {
                "name": name,
                "value": getattr(parameter, "value", None),
                "active": bool(getattr(parameter, "active", True)),
            }
        )
    return entries


def resolve_layer_context(layer):
    if layer is None:
        return None
    glyph = getattr(layer, "parent", None)
    font = getattr(glyph, "parent", None) if glyph is not None else None
    master = getattr(layer, "master", None)
    width = getattr(layer, "width", None)
    if glyph is None or font is None or master is None:
        return None
    try:
        width = float(width)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(width) or width <= 0:
        return None
    return LayerContext(layer, glyph, font, master, width)


def _window_controller(controller):
    if controller is None:
        return None
    try:
        view = _object_value(controller, "view")
        window = _object_value(view, "window")
        return _object_value(window, "windowController")
    except (AttributeError, TypeError):
        return None


def _active_event_tool(controller):
    """Return the tool currently handling events, including temporary tools."""

    window_controller = _window_controller(controller)
    if window_controller is None:
        return None
    for name in ("toolEventDelegate", "toolEventDelegateSelected", "toolDrawDelegate"):
        try:
            tool = _object_value(window_controller, name)
        except Exception:
            continue
        if tool is not None:
            return tool
    return None


def _same_native_object(left, right):
    if left is right:
        return True
    try:
        return bool(left == right)
    except Exception:
        return False


def _tool_candidates(controller):
    """Return the active tool and any selected subtool without losing identity."""

    root = _active_event_tool(controller)
    if root is None:
        return ()

    candidates = []
    pending = [root]
    while pending and len(candidates) < 8:
        candidate = pending.pop(0)
        if candidate is None or any(
            _same_native_object(candidate, existing) for existing in candidates
        ):
            continue
        candidates.append(candidate)
        for name in ("currentTool", "eventHandler"):
            try:
                nested = _object_value(candidate, name)
            except Exception:
                continue
            if nested is not None:
                pending.append(nested)
    return tuple(candidates)


def _tool_class_name(tool):
    try:
        name = _object_value(tool, "className")
        if name:
            return str(name)
    except (AttributeError, TypeError):
        pass
    try:
        return str(tool.__class__.__name__)
    except (AttributeError, TypeError):
        return ""


def _tool_is_kind(controller, class_lookup, class_names):
    tools = _tool_candidates(controller)
    if not tools:
        return False
    for tool in tools:
        tool_name = _tool_class_name(tool)
        for class_name in class_names:
            if tool_name == class_name:
                return True
            try:
                tool_class = class_lookup(class_name)
            except (AttributeError, TypeError):
                tool_class = None
            try:
                if tool_class is not None and tool.isKindOfClass_(tool_class):
                    return True
            except (AttributeError, TypeError):
                continue
    return False


def tool_is_annotation(controller, class_lookup):
    """Return whether the active tool creates annotations rather than outlines."""

    return _tool_is_kind(controller, class_lookup, ("AnnotationTool",))


def tool_is_shape_drawing(controller, class_lookup):
    """Return whether the active tool creates rectangle or circle outlines."""

    if tool_is_annotation(controller, class_lookup):
        return False
    return _tool_is_kind(
        controller,
        class_lookup,
        (
            "GlyphsToolPrimitives",
            "GlyphsToolPrimitivesRect",
            "GlyphsToolPrimitivesCircle",
        ),
    )


def tool_is_outline_creation(controller, class_lookup):
    """Return whether a built-in Draw, Pencil, or primitive tool creates outlines."""

    if tool_is_annotation(controller, class_lookup):
        return False
    if tool_is_shape_drawing(controller, class_lookup):
        return True
    return _tool_is_kind(
        controller,
        class_lookup,
        ("GlyphsToolDraw", "PenTool"),
    )


def tool_is_freehand_drawing(controller, class_lookup):
    """Return whether Glyphs' Pencil tool is recording a freehand stroke."""

    if tool_is_annotation(controller, class_lookup):
        return False
    return _tool_is_kind(controller, class_lookup, ("PenTool",))


def tool_uses_creation_hover(controller, class_lookup):
    """Return whether passive pointer alignment belongs to the active tool."""

    if tool_is_annotation(controller, class_lookup):
        return False
    if tool_is_shape_drawing(controller, class_lookup):
        return True
    return _tool_is_kind(controller, class_lookup, ("GlyphsToolDraw",))


def active_mouse_context(controller, notification):
    """Return ``(active layer, glyph-space point)`` for a Glyphs mouse event."""

    if controller is None or notification is None:
        return None
    try:
        view = _object_value(controller, "graphicView")
    except Exception:
        return None
    try:
        event = _object_value(notification, "object")
    except Exception:
        event = notification
    try:
        view_window = _object_value(view, "window")
        event_window = _object_value(event, "window")
    except Exception:
        view_window = None
        event_window = None
    if (
        view_window is not None
        and event_window is not None
        and not _same_native_object(view_window, event_window)
    ):
        return None
    try:
        layer = _object_value(view, "activeLayer")
        point = view.getActiveLocation_(event)
    except Exception:
        return None
    point = _point_tuple(point)
    if layer is None or point is None:
        return None
    return layer, point


def _optional_tool_value(tool, name):
    try:
        return _object_value(tool, name)
    except Exception:
        pass
    try:
        value_for_key = getattr(tool, "valueForKey_")
        return value_for_key(name)
    except Exception:
        return None


def _dragging_tool(controller):
    for tool in _tool_candidates(controller):
        try:
            if bool(_object_value(tool, "dragging")):
                return tool
        except Exception:
            continue
    return None


def tool_creation_drag_point(controller, class_lookup):
    """Return a live native construction point, never a passive cursor point."""

    if not tool_is_outline_creation(controller, class_lookup):
        return None

    if tool_is_freehand_drawing(controller, class_lookup):
        for tool in _tool_candidates(controller):
            drag_points = _optional_tool_value(tool, "dragPoints")
            if drag_points is None:
                continue
            count = _optional_tool_value(drag_points, "count")
            if count is None:
                try:
                    count = len(drag_points)
                except (TypeError, AttributeError):
                    count = 0
            try:
                active = int(count) >= 2
            except (TypeError, ValueError, OverflowError):
                active = False
            if not active:
                continue
            point = _point_tuple(_optional_tool_value(drag_points, "lastPoint"))
            if point is not None:
                return point
        return None

    dragging_tool = _dragging_tool(controller)
    if dragging_tool is None:
        return None

    if tool_is_shape_drawing(controller, class_lookup):
        names = ("selectionDrag", "auswahlDrag", "dragCurrent", "draggCurrent")
    else:
        names = ("dragCurrent", "draggCurrent", "selectionDrag", "auswahlDrag")

    tools = (dragging_tool,) + tuple(
        tool
        for tool in _tool_candidates(controller)
        if not _same_native_object(tool, dragging_tool)
    )
    for tool in tools:
        for name in names:
            point = _point_tuple(_optional_tool_value(tool, name))
            if point is not None:
                return point
    return None


def tool_allows_drawing(controller, class_lookup):
    if controller is None:
        return True
    return not _tool_is_kind(
        controller,
        class_lookup,
        ("GlyphsToolText", "GlyphsToolHand", "GlyphsToolZoom"),
    )


def tool_is_drawing(controller, class_lookup):
    """Return whether the active tool can add outline nodes during this drag."""

    return tool_is_outline_creation(controller, class_lookup)


def tool_is_dragging(controller):
    """Return Glyphs' native edit-tool drag state, never cursor-move state."""

    return _dragging_tool(controller) is not None


def tool_drag_session(controller):
    """Return a stable native-tool/drag-origin pair for the active drag."""

    tool = _dragging_tool(controller)
    if tool is None:
        return None
    try:
        drag_start = _point_tuple(_object_value(tool, "dragStart"))
    except Exception:
        drag_start = None
    return tool, drag_start


def _object_value(owner, name):
    value = getattr(owner, name)
    return value() if callable(value) else value


def _point_tuple(point):
    try:
        unboxed = _object_value(point, "pointValue")
    except Exception:
        unboxed = None
    if unboxed is not None and unboxed is not point:
        point = unboxed
    try:
        x = float(point.x)
        y = float(point.y)
    except AttributeError:
        try:
            x = float(point[0])
            y = float(point[1])
        except (TypeError, ValueError, OverflowError, IndexError):
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def selected_node_records(layer, class_lookup):
    """Return retained ``(node, point)`` records for selected GSNode objects."""

    if layer is None:
        return ()
    try:
        selection = _object_value(layer, "selection")
        candidates = iter(selection)
    except (AttributeError, TypeError):
        return ()

    try:
        node_class = class_lookup("GSNode")
    except (AttributeError, TypeError):
        node_class = None

    records = []
    seen = set()
    for candidate in candidates:
        if node_class is not None:
            try:
                if not candidate.isKindOfClass_(node_class):
                    continue
            except (AttributeError, TypeError):
                continue
        elif candidate.__class__.__name__ not in ("GSNode", "Node"):
            continue

        try:
            position = _object_value(candidate, "position")
        except (AttributeError, TypeError):
            position = candidate
        point = _point_tuple(position)
        if point is None or candidate in seen:
            continue
        records.append((candidate, point))
        seen.add(candidate)
    return tuple(records)


def selected_node_points(layer, class_lookup):
    """Return finite, deduplicated positions for selected GSNode objects."""

    points = []
    seen = set()
    for _node, point in selected_node_records(layer, class_lookup):
        if point in seen:
            continue
        points.append(point)
        seen.add(point)
    return tuple(points)
