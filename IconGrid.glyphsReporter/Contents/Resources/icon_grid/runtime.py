"""Duck-typed Glyphs runtime adapters, kept importable outside Glyphs."""

from __future__ import absolute_import

import math
from collections import namedtuple


LayerContext = namedtuple("LayerContext", "layer glyph font master width")
MouseContext = namedtuple("MouseContext", "layer point scale")


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


def tool_allows_drawing(controller, class_lookup):
    if controller is None:
        return True
    try:
        window_controller = controller.view().window().windowController()
        if window_controller is None:
            return True
        tool = window_controller.toolDrawDelegate()
        if tool is None:
            return True
        for class_name in ("GlyphsToolText", "GlyphsToolHand"):
            tool_class = class_lookup(class_name)
            if tool_class is not None and tool.isKindOfClass_(tool_class):
                return False
    except (AttributeError, TypeError):
        return True
    return True


def _object_value(owner, name):
    value = getattr(owner, name)
    return value() if callable(value) else value


def _point_tuple(point):
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


def resolve_mouse_context(controller, event):
    """Convert a mouse event to active-layer coordinates without Glyphs imports."""
    if controller is None or event is None:
        return None
    try:
        graphic_view = _object_value(controller, "graphicView")
        view_window = _object_value(graphic_view, "window")
        event_window = _object_value(event, "window")
        if view_window is not None and event_window is not None and view_window != event_window:
            return None
        layer = _object_value(graphic_view, "activeLayer")
        location_method = getattr(graphic_view, "getActiveLocation_")
        point = _point_tuple(location_method(event))
        scale = float(_object_value(graphic_view, "scale"))
    except (AttributeError, TypeError, ValueError, OverflowError):
        return None
    if layer is None or point is None or not math.isfinite(scale) or scale <= 0:
        return None
    return MouseContext(layer, point, scale)
