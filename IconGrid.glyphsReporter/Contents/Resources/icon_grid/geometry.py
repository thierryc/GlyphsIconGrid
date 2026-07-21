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


def canvas_for_origin(width, height, origin):
    width = float(width)
    height = float(height)
    vertical, horizontal = origin.split("-", 1) if "-" in origin else (origin, origin)
    if origin == "center":
        vertical = horizontal = "center"
    horizontal_factor = {"left": 0.0, "center": 0.5, "right": 1.0}[horizontal]
    vertical_factor = {"bottom": 0.0, "center": 0.5, "top": 1.0}[vertical]
    xmin = -horizontal_factor * width
    ymin = -vertical_factor * height
    return Canvas(xmin, ymin, xmin + width, ymin + height)


def _near(a, b):
    return abs(a - b) <= _EPSILON


def _grid_positions(start, end, step, major_every):
    minimum_index = int(math.ceil((start - _EPSILON) / step))
    maximum_index = int(math.floor((end + _EPSILON) / step))
    minor = []
    major = []
    axes = []
    for index in range(minimum_index, maximum_index + 1):
        position = index * step
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
    width = _finite_positive(width)
    height = _finite_positive(getattr(config, "height", None))
    if width is None or height is None:
        return None

    canvas = canvas_for_origin(width, height, config.origin)
    step_x = width / float(config.columns)
    step_y = height / float(config.rows)

    vertical_minor_x, vertical_major_x, vertical_axis_x = _grid_positions(
        canvas.xmin, canvas.xmax, step_x, config.major_every
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

    inset_x = min(config.padding * step_x, width / 2.0)
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
