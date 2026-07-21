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
