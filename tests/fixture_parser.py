"""Small parser for the controlled OpenStep-style release fixtures."""

from __future__ import absolute_import

import re


def _balanced(source, start, opening, closing):
    depth = 0
    quoted = False
    escaped = False
    for index in range(start, len(source)):
        character = source[index]
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == '"':
            quoted = True
        elif character == opening:
            depth += 1
        elif character == closing:
            depth -= 1
            if depth == 0:
                return source[start + 1:index], index + 1
    raise ValueError("unbalanced {}{}".format(opening, closing))


def _assignment(source, name):
    match = re.search(r"(?:^|\n){} = ([^;]+);".format(re.escape(name)), source)
    return match.group(1).strip() if match else None


def _scalar(raw):
    if raw is None:
        return None
    if len(raw) >= 2 and raw[0] == raw[-1] == '"':
        return raw[1:-1]
    if raw in ("true", "YES"):
        return True
    if raw in ("false", "NO"):
        return False
    try:
        number = float(raw)
    except ValueError:
        return raw
    return int(number) if number.is_integer() else number


def _array_after(source, marker):
    match = re.search(re.escape(marker) + r"\s*\(", source)
    if not match:
        return None
    start = match.end() - 1
    return _balanced(source, start, "(", ")")[0]


def _top_level_records(array_source):
    records = []
    index = 0
    while index < len(array_source):
        if array_source[index] != "{":
            index += 1
            continue
        record, end = _balanced(array_source, index, "{", "}")
        records.append(record)
        index = end
    return records


def _parameters(owner_source):
    array = _array_after(owner_source, "customParameters =")
    if array is None:
        return []
    records = []
    for record in _top_level_records(array):
        name = _scalar(_assignment(record, "name"))
        if not isinstance(name, str) or not name.startswith("IconGrid."):
            continue
        records.append(
            {
                "name": name,
                "value": _scalar(_assignment(record, "value")),
                "active": _assignment(record, "disabled") not in ("1", "true", "YES"),
            }
        )
    return records


def parse_fixture(path):
    with open(path, "r", encoding="utf-8") as handle:
        source = handle.read()
    master_marker = re.search(r"(?:^|\n)fontMaster = \(", source)
    if not master_marker:
        raise ValueError("fixture has no fontMaster array")
    font_source = source[:master_marker.start()]
    masters_array = _array_after(source, "fontMaster =")
    masters = {}
    for master_source in _top_level_records(masters_array):
        master_id = str(_scalar(_assignment(master_source, "id")))
        masters[master_id] = {
            "id": master_id,
            "name": str(_scalar(_assignment(master_source, "name"))),
            "parameters": _parameters(master_source),
        }
    return {
        "familyName": _scalar(_assignment(source, "familyName")),
        "unitsPerEm": _scalar(_assignment(source, "unitsPerEm")),
        "fontParameters": _parameters(font_source),
        "masters": masters,
    }
