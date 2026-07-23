"""Resolve IconGrid custom parameters without depending on Glyphs or AppKit."""

from __future__ import absolute_import

import math
from collections.abc import Mapping


PREFIX = "IconGrid."
DEFAULT_GRID_COLOR = (10.0 / 255.0, 132.0 / 255.0, 1.0)
ORIGINS = (
    "bottom-left",
    "bottom-center",
    "bottom-right",
    "center-left",
    "center",
    "center-right",
    "top-left",
    "top-center",
    "top-right",
)
GRID_MODES = ("odd", "even")
PARAMETER_NAMES = (
    "IconGrid.columns",
    "IconGrid.rows",
    "IconGrid.gridSize",
    "IconGrid.gridMode",
    "IconGrid.width",
    "IconGrid.height",
    "IconGrid.origin",
    "IconGrid.baselineOffset",
    "IconGrid.padding",
    "IconGrid.majorEvery",
    "IconGrid.rings",
    "IconGrid.spokes",
    "IconGrid.showKeylines",
    "IconGrid.color",
    "IconGrid.opacity",
    "IconGrid.alignmentHighlight",
    "IconGrid.alignmentTolerance",
)

DEFAULTS = {
    "columns": 24,
    "rows": 24,
    "grid_size": None,
    "grid_mode": "odd",
    "origin": "bottom-center",
    "baseline_offset": 0.0,
    "padding": 2.0,
    "major_every": 4,
    "spokes": 8,
    "show_keylines": True,
    "color": DEFAULT_GRID_COLOR,
    "opacity": 0.28,
    "alignment_highlight": True,
    "alignment_tolerance": 2.0,
}

MAX_DIVISIONS = 256
MAX_RINGS = 128
MAX_SPOKES = 360
MIN_ALIGNMENT_TOLERANCE = 1.0
MAX_ALIGNMENT_TOLERANCE = 20.0
MAX_AUTOMATIC_METRIC = 1000000.0


class GridConfig(object):
    """Validated immutable-by-convention grid configuration."""

    __slots__ = (
        "columns",
        "rows",
        "grid_size",
        "grid_mode",
        "height",
        "width",
        "origin",
        "baseline_offset",
        "padding",
        "major_every",
        "rings",
        "spokes",
        "show_keylines",
        "color",
        "opacity",
        "alignment_highlight",
        "alignment_tolerance",
        "metric_top",
        "metric_bottom",
    )

    def __init__(
        self,
        columns,
        rows,
        grid_size,
        grid_mode,
        height,
        width,
        origin,
        baseline_offset,
        padding,
        major_every,
        rings,
        spokes,
        show_keylines,
        color,
        opacity,
        alignment_highlight,
        alignment_tolerance,
        metric_top,
        metric_bottom,
    ):
        self.columns = columns
        self.rows = rows
        self.grid_size = grid_size
        self.grid_mode = grid_mode
        self.height = height
        self.width = width
        self.origin = origin
        self.baseline_offset = baseline_offset
        self.padding = padding
        self.major_every = major_every
        self.rings = rings
        self.spokes = spokes
        self.show_keylines = show_keylines
        self.color = color
        self.opacity = opacity
        self.alignment_highlight = alignment_highlight
        self.alignment_tolerance = alignment_tolerance
        self.metric_top = metric_top
        self.metric_bottom = metric_bottom


def _finite_number(value):
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _record_parts(record):
    if isinstance(record, Mapping):
        return (
            record.get("name"),
            record.get("value"),
            record.get("active", True),
        )
    try:
        if len(record) == 2:
            return record[0], record[1], True
        return record[0], record[1], record[2]
    except (TypeError, IndexError, KeyError):
        return None, None, False


def _parameter_map(parameters, label):
    if parameters is None:
        return {}, []
    if isinstance(parameters, Mapping):
        return {
            str(name): value
            for name, value in parameters.items()
            if str(name).startswith(PREFIX)
        }, []

    values = {}
    warnings = []
    try:
        records = iter(parameters)
    except TypeError:
        return {}, ["{} custom parameters are not iterable".format(label)]

    for record in records:
        name, value, active = _record_parts(record)
        if not isinstance(name, str) or not name.startswith(PREFIX) or not active:
            continue
        if name in values:
            warnings.append("{} has duplicate active parameter {}; last value wins".format(label, name))
        values[name] = value
    return values, warnings


def _integer_parser(minimum, maximum):
    def parse(value):
        number = _finite_number(value)
        if number is None or int(number) != number:
            return False, None, None
        integer = int(number)
        if integer < minimum or integer > maximum:
            return False, None, None
        return True, integer, None
    return parse


def _positive_number(value):
    number = _finite_number(value)
    if number is None or number <= 0:
        return False, None, None
    return True, number, None


def _number(value):
    number = _finite_number(value)
    if number is None:
        return False, None, None
    return True, number, None


def _nonnegative_number(value):
    number = _finite_number(value)
    if number is None or number < 0:
        return False, None, None
    return True, number, None


def _number_in_range(minimum, maximum):
    def parse(value):
        number = _finite_number(value)
        if number is None or number < minimum or number > maximum:
            return False, None, None
        return True, number, None
    return parse


def _grid_size_parser(minimum):
    def parse(value):
        number = _finite_number(value)
        if number is None or number <= 0 or number < minimum:
            return False, None, None
        return True, number, None
    return parse


def _origin(value):
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ORIGINS:
            return True, normalized, None
    return False, None, None


def _grid_mode(value):
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in GRID_MODES:
            return True, normalized, None
    return False, None, None


def _boolean(value):
    if isinstance(value, bool):
        return True, value, None
    if isinstance(value, (int, float)) and value in (0, 1):
        return True, bool(value), None
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ("true", "yes", "on", "1"):
            return True, True, None
        if normalized in ("false", "no", "off", "0"):
            return True, False, None
    return False, None, None


def _color(value):
    if not isinstance(value, str):
        return False, None, None
    normalized = value.strip()
    semantic = normalized.lower()
    if semantic in ("accent", "grid", "label", "separator"):
        return True, semantic, None
    if len(normalized) != 7 or not normalized.startswith("#"):
        return False, None, None
    try:
        channels = tuple(int(normalized[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    except ValueError:
        return False, None, None
    return True, channels, None


def _opacity(value):
    number = _finite_number(value)
    if number is None:
        return False, None, None
    clamped = min(1.0, max(0.0, number))
    note = "clamped to {:.3g}".format(clamped) if clamped != number else None
    return True, clamped, note


def _fallback_square_size(cap_height, upm):
    upm_ok, resolved_upm, _note = _positive_number(upm)
    if upm_ok and resolved_upm <= MAX_AUTOMATIC_METRIC:
        return resolved_upm
    cap_ok, resolved_cap_height, _note = _positive_number(cap_height)
    if cap_ok and resolved_cap_height <= MAX_AUTOMATIC_METRIC:
        return resolved_cap_height
    return 1000.0


def _bounded_metric(value, upm, positive=False):
    number = _finite_number(value)
    if number is None or (positive and number <= 0):
        return None
    upm_ok, resolved_upm, _note = _positive_number(upm)
    maximum = (
        min(MAX_AUTOMATIC_METRIC, resolved_upm * 10.0)
        if upm_ok
        else MAX_AUTOMATIC_METRIC
    )
    if abs(number) > maximum:
        return None
    return number


def _choose(name, parser, master, font, fallback, warnings):
    key = PREFIX + name
    for label, source in (("master", master), ("font", font)):
        if key not in source:
            continue
        ok, parsed, note = parser(source[key])
        if ok:
            if note:
                warnings.append("{} {} {}".format(label, key, note))
            return parsed
        warnings.append("Ignoring invalid {} value for {}: {!r}".format(label, key, source[key]))
    return fallback


def resolve_config(
    font_parameters,
    master_parameters,
    master_cap_height,
    font_upm,
    master_x_height=None,
    master_ascender=None,
    master_descender=None,
):
    """Return ``(GridConfig, warnings)`` using master-over-font precedence."""

    font, font_warnings = _parameter_map(font_parameters, "font")
    master, master_warnings = _parameter_map(master_parameters, "master")
    warnings = font_warnings + master_warnings

    square_size = _fallback_square_size(master_cap_height, font_upm)
    columns = _choose(
        "columns", _integer_parser(1, MAX_DIVISIONS), master, font, DEFAULTS["columns"], warnings
    )
    rows = _choose("rows", _integer_parser(1, MAX_DIVISIONS), master, font, DEFAULTS["rows"], warnings)
    height = _choose("height", _positive_number, master, font, square_size, warnings)
    width = _choose("width", _positive_number, master, font, square_size, warnings)
    minimum_grid_size = max(width, height) / float(MAX_DIVISIONS)
    grid_size = _choose(
        "gridSize",
        _grid_size_parser(minimum_grid_size),
        master,
        font,
        DEFAULTS["grid_size"],
        warnings,
    )
    grid_mode = _choose(
        "gridMode", _grid_mode, master, font, DEFAULTS["grid_mode"], warnings
    )
    origin = _choose("origin", _origin, master, font, DEFAULTS["origin"], warnings)
    x_height = _bounded_metric(master_x_height, font_upm, positive=True)
    default_baseline_offset = DEFAULTS["baseline_offset"]
    if origin == DEFAULTS["origin"] and x_height is not None:
        default_baseline_offset = (height - x_height) / 2.0
    baseline_offset = _choose(
        "baselineOffset", _number, master, font, default_baseline_offset, warnings
    )
    padding = _choose("padding", _nonnegative_number, master, font, DEFAULTS["padding"], warnings)
    major_every = _choose("majorEvery", _integer_parser(0, MAX_DIVISIONS), master, font, DEFAULTS["major_every"], warnings)
    spokes = _choose("spokes", _integer_parser(0, MAX_SPOKES), master, font, DEFAULTS["spokes"], warnings)
    show_keylines = _choose("showKeylines", _boolean, master, font, DEFAULTS["show_keylines"], warnings)
    color = _choose("color", _color, master, font, DEFAULTS["color"], warnings)
    opacity = _choose("opacity", _opacity, master, font, DEFAULTS["opacity"], warnings)
    alignment_highlight = _choose(
        "alignmentHighlight",
        _boolean,
        master,
        font,
        DEFAULTS["alignment_highlight"],
        warnings,
    )
    alignment_tolerance = _choose(
        "alignmentTolerance",
        _number_in_range(MIN_ALIGNMENT_TOLERANCE, MAX_ALIGNMENT_TOLERANCE),
        master,
        font,
        DEFAULTS["alignment_tolerance"],
        warnings,
    )

    step_x = grid_size if grid_size is not None else width / float(columns)
    step_y = grid_size if grid_size is not None else height / float(rows)
    usable_cell_span = min(width / step_x, height / step_y)
    maximum_padding = max(0.0, (usable_cell_span - 1.0) / 2.0)
    if padding > maximum_padding:
        warnings.append(
            "IconGrid.padding clamped from {!r} to {!r}".format(padding, maximum_padding)
        )
        padding = maximum_padding

    automatic_rings = max(0, int(math.floor(min(columns, rows) / 2.0 - padding)))
    rings = _choose("rings", _integer_parser(0, MAX_RINGS), master, font, automatic_rings, warnings)

    metric_candidates = (
        _bounded_metric(master_cap_height, font_upm, positive=True),
        _bounded_metric(master_ascender, font_upm, positive=True),
    )
    metric_top_values = [value for value in metric_candidates if value is not None]
    metric_top = max(metric_top_values) if metric_top_values else None
    metric_bottom = _bounded_metric(master_descender, font_upm)

    return GridConfig(
        columns=columns,
        rows=rows,
        grid_size=grid_size,
        grid_mode=grid_mode,
        height=height,
        width=width,
        origin=origin,
        baseline_offset=baseline_offset,
        padding=padding,
        major_every=major_every,
        rings=rings,
        spokes=spokes,
        show_keylines=show_keylines,
        color=color,
        opacity=opacity,
        alignment_highlight=alignment_highlight,
        alignment_tolerance=alignment_tolerance,
        metric_top=metric_top,
        metric_bottom=metric_bottom,
    ), warnings
