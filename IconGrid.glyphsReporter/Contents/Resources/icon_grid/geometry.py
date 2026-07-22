"""Deterministic IconGrid geometry with no Glyphs or AppKit dependencies."""

from __future__ import absolute_import

import math
from collections import namedtuple


_EPSILON = 1e-9


class Canvas(namedtuple("CanvasBase", "xmin ymin xmax ymax")):
    __slots__ = ()

    @property
    def width(self):
        return self.xmax - self.xmin

    @property
    def height(self):
        return self.ymax - self.ymin

    @property
    def center(self):
        return ((self.xmin + self.xmax) / 2.0, (self.ymin + self.ymax) / 2.0)

    def as_tuple(self):
        return tuple(self)


Line = namedtuple("Line", "x1 y1 x2 y2")
Circle = namedtuple("Circle", "cx cy radius")
Keyline = namedtuple("Keyline", "name shape x y width height")
GuideRef = namedtuple("GuideRef", "kind index")


class GridGeometry(object):
    __slots__ = (
        "canvas",
        "live_area",
        "center",
        "live_radius",
        "minor_lines",
        "major_lines",
        "axis_lines",
        "frames",
        "rings",
        "spokes",
        "keylines",
    )

    def __init__(
        self,
        canvas,
        live_area,
        minor_lines,
        major_lines,
        axis_lines,
        frames,
        rings,
        spokes,
        keylines,
    ):
        self.canvas = canvas
        self.live_area = live_area
        self.center = canvas.center
        self.live_radius = min(live_area.width, live_area.height) / 2.0
        self.minor_lines = minor_lines
        self.major_lines = major_lines
        self.axis_lines = axis_lines
        self.frames = frames
        self.rings = rings
        self.spokes = spokes
        self.keylines = keylines

    def all_grid_lines(self):
        return self.minor_lines + self.major_lines + self.axis_lines


def _finite_positive(value):
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number) or number <= 0:
        return None
    return number


def _origin_parts(origin):
    if origin == "center":
        return "center", "center"
    return origin.split("-", 1)


def canvas_for_origin(width, height, origin, anchor_width=None):
    """Place a fixed canvas against an advance-width horizontal anchor."""
    width = float(width)
    height = float(height)
    anchor_width = width if anchor_width is None else float(anchor_width)
    vertical, horizontal = _origin_parts(origin)
    horizontal_factor = {"left": 0.0, "center": 0.5, "right": 1.0}[horizontal]
    vertical_factor = {"bottom": 0.0, "center": 0.5, "top": 1.0}[vertical]
    horizontal_anchor = horizontal_factor * anchor_width
    xmin = horizontal_anchor - horizontal_factor * width
    ymin = -vertical_factor * height
    return Canvas(xmin, ymin, xmin + width, ymin + height)


def _near(a, b):
    return abs(a - b) <= _EPSILON


def _grid_positions(start, end, step, major_every, anchor=0.0):
    minimum_index = int(math.ceil((start - anchor - _EPSILON) / step))
    maximum_index = int(math.floor((end - anchor + _EPSILON) / step))
    minor = []
    major = []
    axes = []
    for index in range(minimum_index, maximum_index + 1):
        position = anchor + index * step
        is_axis = index == 0
        is_boundary = _near(position, start) or _near(position, end)
        if is_boundary and not is_axis:
            continue
        if is_axis:
            axes.append(position)
        elif major_every and abs(index) % major_every == 0:
            major.append(position)
        else:
            minor.append(position)
    return minor, major, axes


def _rect_keyline(name, cx, cy, width, height):
    return Keyline(name, "rect", cx - width / 2.0, cy - height / 2.0, width, height)


def build_geometry(width, config):
    layer_width = _finite_positive(width)
    height = _finite_positive(getattr(config, "height", None))
    grid_width = _finite_positive(getattr(config, "width", height))
    if layer_width is None or height is None or grid_width is None:
        return None

    _vertical_origin, horizontal_origin = _origin_parts(config.origin)
    horizontal_factor = {"left": 0.0, "center": 0.5, "right": 1.0}[horizontal_origin]
    horizontal_anchor = horizontal_factor * layer_width
    canvas = canvas_for_origin(
        grid_width, height, config.origin, anchor_width=layer_width
    )
    baseline_offset = float(getattr(config, "baseline_offset", 0.0))
    canvas = Canvas(
        canvas.xmin,
        canvas.ymin - baseline_offset,
        canvas.xmax,
        canvas.ymax - baseline_offset,
    )
    step_x = grid_width / float(config.columns)
    step_y = height / float(config.rows)

    vertical_minor_x, vertical_major_x, vertical_axis_x = _grid_positions(
        canvas.xmin, canvas.xmax, step_x, config.major_every, horizontal_anchor
    )
    horizontal_minor_y, horizontal_major_y, horizontal_axis_y = _grid_positions(
        canvas.ymin, canvas.ymax, step_y, config.major_every
    )
    vertical_minor = [Line(x, canvas.ymin, x, canvas.ymax) for x in vertical_minor_x]
    vertical_major = [Line(x, canvas.ymin, x, canvas.ymax) for x in vertical_major_x]
    vertical_axes = [Line(x, canvas.ymin, x, canvas.ymax) for x in vertical_axis_x]
    horizontal_minor = [Line(canvas.xmin, y, canvas.xmax, y) for y in horizontal_minor_y]
    horizontal_major = [Line(canvas.xmin, y, canvas.xmax, y) for y in horizontal_major_y]
    horizontal_axes = [Line(canvas.xmin, y, canvas.xmax, y) for y in horizontal_axis_y]

    inset_x = min(config.padding * step_x, grid_width / 2.0)
    inset_y = min(config.padding * step_y, height / 2.0)
    live_area = Canvas(
        canvas.xmin + inset_x,
        canvas.ymin + inset_y,
        canvas.xmax - inset_x,
        canvas.ymax - inset_y,
    )
    live_radius = max(0.0, min(live_area.width, live_area.height) / 2.0)
    center_x, center_y = canvas.center

    rings = []
    if config.rings > 0 and live_radius > 0:
        rings = [
            Circle(center_x, center_y, live_radius * index / float(config.rings))
            for index in range(1, config.rings + 1)
        ]

    spokes = []
    if config.spokes > 0 and live_radius > 0:
        for index in range(config.spokes):
            angle = 2.0 * math.pi * index / float(config.spokes)
            spokes.append(
                Line(
                    center_x,
                    center_y,
                    center_x + math.cos(angle) * live_radius,
                    center_y + math.sin(angle) * live_radius,
                )
            )

    keylines = []
    if config.show_keylines and live_radius > 0:
        diameter = live_radius * 2.0
        keylines = [
            Keyline("circle", "circle", center_x - live_radius, center_y - live_radius, diameter, diameter),
            _rect_keyline("square", center_x, center_y, diameter * 0.9, diameter * 0.9),
            _rect_keyline("portrait", center_x, center_y, diameter * 0.8, diameter),
            _rect_keyline("landscape", center_x, center_y, diameter, diameter * 0.8),
        ]

    return GridGeometry(
        canvas=canvas,
        live_area=live_area,
        minor_lines=vertical_minor + horizontal_minor,
        major_lines=vertical_major + horizontal_major,
        axis_lines=vertical_axes + horizontal_axes,
        frames=[canvas, live_area],
        rings=rings,
        spokes=spokes,
        keylines=keylines,
    )


def line_width_for_scale(screen_pixels, scale):
    pixels = _finite_positive(screen_pixels) or 1.0
    resolved_scale = _finite_positive(scale) or 1.0
    return pixels / resolved_scale


def _finite_point(point):
    if point is None:
        return None
    try:
        x, y = point
        x = float(x)
        y = float(y)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return x, y


def _distance_to_segment(point, line):
    px, py = point
    dx = line.x2 - line.x1
    dy = line.y2 - line.y1
    length_squared = dx * dx + dy * dy
    if length_squared <= _EPSILON:
        return math.hypot(px - line.x1, py - line.y1)
    projection = ((px - line.x1) * dx + (py - line.y1) * dy) / length_squared
    projection = min(1.0, max(0.0, projection))
    closest_x = line.x1 + projection * dx
    closest_y = line.y1 + projection * dy
    return math.hypot(px - closest_x, py - closest_y)


def _frame_edges(frame):
    return (
        Line(frame.xmin, frame.ymin, frame.xmax, frame.ymin),
        Line(frame.xmax, frame.ymin, frame.xmax, frame.ymax),
        Line(frame.xmax, frame.ymax, frame.xmin, frame.ymax),
        Line(frame.xmin, frame.ymax, frame.xmin, frame.ymin),
    )


def _distance_to_frame(point, frame):
    return min(_distance_to_segment(point, edge) for edge in _frame_edges(frame))


def _distance_to_circle(point, circle):
    return abs(math.hypot(point[0] - circle.cx, point[1] - circle.cy) - circle.radius)


def _keyline_primitive(keyline):
    if keyline.shape == "circle":
        return Circle(
            keyline.x + keyline.width / 2.0,
            keyline.y + keyline.height / 2.0,
            min(keyline.width, keyline.height) / 2.0,
        )
    return Canvas(keyline.x, keyline.y, keyline.x + keyline.width, keyline.y + keyline.height)


def _signature_number(value):
    return round(float(value), 12)


def _line_signature(line):
    start = (_signature_number(line.x1), _signature_number(line.y1))
    end = (_signature_number(line.x2), _signature_number(line.y2))
    if end < start:
        start, end = end, start
    return ("line",) + start + end


def _circle_signature(circle):
    return (
        "circle",
        _signature_number(circle.cx),
        _signature_number(circle.cy),
        _signature_number(circle.radius),
    )


def _frame_signature(frame):
    return ("frame",) + tuple(_signature_number(value) for value in frame)


def _guide_catalog(geometry):
    for kind, items in (
        ("minor", geometry.minor_lines),
        ("major", geometry.major_lines),
        ("axis", geometry.axis_lines),
        ("frame", geometry.frames),
        ("ring", geometry.rings),
        ("spoke", geometry.spokes),
        ("keyline", geometry.keylines),
    ):
        for index, item in enumerate(items):
            primitive = _keyline_primitive(item) if kind == "keyline" else item
            if isinstance(primitive, Line):
                signature = _line_signature(primitive)
                distance = _distance_to_segment
            elif isinstance(primitive, Circle):
                signature = _circle_signature(primitive)
                distance = _distance_to_circle
            else:
                signature = _frame_signature(primitive)
                distance = _distance_to_frame
            yield GuideRef(kind, index), primitive, signature, distance


def hit_test_guides(geometry, point, tolerance):
    """Return stable visible-guide references within a glyph-unit tolerance."""
    if geometry is None:
        return ()
    resolved_point = _finite_point(point)
    try:
        resolved_tolerance = float(tolerance)
    except (TypeError, ValueError, OverflowError):
        return ()
    if (
        resolved_point is None
        or not math.isfinite(resolved_tolerance)
        or resolved_tolerance < 0
    ):
        return ()

    hits = []
    seen = set()
    for reference, primitive, signature, distance in _guide_catalog(geometry):
        if signature in seen:
            continue
        if distance(resolved_point, primitive) <= resolved_tolerance + _EPSILON:
            hits.append(reference)
            seen.add(signature)
    return tuple(hits)


def _round(value):
    return round(float(value), 6)


def snapshot(geometry):
    """Return stable plain data suitable for regression tests."""
    return {
        "canvas": [_round(value) for value in geometry.canvas],
        "liveArea": [_round(value) for value in geometry.live_area],
        "center": [_round(value) for value in geometry.center],
        "minor": [[_round(value) for value in line] for line in geometry.minor_lines],
        "major": [[_round(value) for value in line] for line in geometry.major_lines],
        "axes": [[_round(value) for value in line] for line in geometry.axis_lines],
        "rings": [[_round(circle.cx), _round(circle.cy), _round(circle.radius)] for circle in geometry.rings],
        "spokes": [[_round(value) for value in line] for line in geometry.spokes],
        "keylines": [
            [shape.name, shape.shape, _round(shape.x), _round(shape.y), _round(shape.width), _round(shape.height)]
            for shape in geometry.keylines
        ],
    }
