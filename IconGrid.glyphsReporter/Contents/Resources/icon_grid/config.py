"""Resolve IconGrid custom parameters without depending on Glyphs or AppKit."""

from __future__ import absolute_import

import math
from collections.abc import Mapping


PREFIX = "IconGrid."
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

DEFAULTS = {
    "columns": 24,
    "rows": 24,
    "origin": "bottom-left",
    "baseline_offset": 0.0,
    "padding": 2.0,
    "major_every": 4,
    "spokes": 8,
    "show_keylines": True,
    "color": "accent",
    "opacity": 0.28,
    "hover_highlight": True,
    "hover_tolerance": 5.0,
}

MAX_DIVISIONS = 256
MAX_RINGS = 128
MAX_SPOKES = 360
MIN_HOVER_TOLERANCE = 1.0
MAX_HOVER_TOLERANCE = 20.0


class GridConfig(object):
    """Validated immutable-by-convention grid configuration."""

    __slots__ = (
        "columns",
        "rows",
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
        "hover_highlight",
        "hover_tolerance",
    )

    def __init__(
        self,
        columns,
        rows,
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
        hover_highlight,
        hover_tolerance,
    ):
        self.columns = columns
        self.rows = rows
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
        self.hover_highlight = hover_highlight
        self.hover_tolerance = hover_tolerance


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


def _origin(value):
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in ORIGINS:
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


def _fallback_height(cap_height, upm):
    for value in (cap_height, upm, 1000):
        ok, number, _note = _positive_number(value)
        if ok:
            return number
    return 1000.0


def _fallback_width(upm):
    for value in (upm, 1000):
        ok, number, _note = _positive_number(value)
        if ok:
            return number * 1.5
    return 1500.0


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
):
    """Return ``(GridConfig, warnings)`` using master-over-font precedence."""

    font, font_warnings = _parameter_map(font_parameters, "font")
    master, master_warnings = _parameter_map(master_parameters, "master")
    warnings = font_warnings + master_warnings

    columns = _choose("columns", _integer_parser(1, MAX_DIVISIONS), master, font, DEFAULTS["columns"], warnings)
    rows = _choose("rows", _integer_parser(1, MAX_DIVISIONS), master, font, DEFAULTS["rows"], warnings)
    height = _choose("height", _positive_number, master, font, _fallback_height(master_cap_height, font_upm), warnings)
    width = _choose("width", _positive_number, master, font, _fallback_width(font_upm), warnings)
    origin = _choose("origin", _origin, master, font, DEFAULTS["origin"], warnings)
    baseline_offset = _choose(
        "baselineOffset", _number, master, font, DEFAULTS["baseline_offset"], warnings
    )
    padding = _choose("padding", _nonnegative_number, master, font, DEFAULTS["padding"], warnings)
    major_every = _choose("majorEvery", _integer_parser(0, MAX_DIVISIONS), master, font, DEFAULTS["major_every"], warnings)
    spokes = _choose("spokes", _integer_parser(0, MAX_SPOKES), master, font, DEFAULTS["spokes"], warnings)
    show_keylines = _choose("showKeylines", _boolean, master, font, DEFAULTS["show_keylines"], warnings)
    color = _choose("color", _color, master, font, DEFAULTS["color"], warnings)
    opacity = _choose("opacity", _opacity, master, font, DEFAULTS["opacity"], warnings)
    hover_highlight = _choose(
        "hoverHighlight", _boolean, master, font, DEFAULTS["hover_highlight"], warnings
    )
    hover_tolerance = _choose(
        "hoverTolerance",
        _number_in_range(MIN_HOVER_TOLERANCE, MAX_HOVER_TOLERANCE),
        master,
        font,
        DEFAULTS["hover_tolerance"],
        warnings,
    )

    maximum_padding = max(0.0, (min(columns, rows) - 1.0) / 2.0)
    if padding > maximum_padding:
        warnings.append(
            "IconGrid.padding clamped from {!r} to {!r}".format(padding, maximum_padding)
        )
        padding = maximum_padding

    automatic_rings = max(0, int(math.floor(min(columns, rows) / 2.0 - padding)))
    rings = _choose("rings", _integer_parser(0, MAX_RINGS), master, font, automatic_rings, warnings)

    return GridConfig(
        columns=columns,
        rows=rows,
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
        hover_highlight=hover_highlight,
        hover_tolerance=hover_tolerance,
    ), warnings
