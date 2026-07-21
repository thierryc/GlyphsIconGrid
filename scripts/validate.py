#!/usr/bin/env python3
"""Static dual-version validation for the IconGrid reporter bundle."""

from __future__ import absolute_import, print_function

import argparse
import ast
import hashlib
import json
import os
import plistlib
import struct
import sys


EXPECTED_ID = "com.thierryc.GlyphsIconGrid"
EXPECTED_CLASS = "GlyphsIconGrid"
EXPECTED_LOADER_SHA256 = "165af5653635741bbf6698476aff5f868618a8040bc76d8abb7076f7115e91fa"
REQUIRED_CPU_TYPES = {0x01000007, 0x0100000C}  # x86_64, arm64


def _python_files(resources):
    for directory, _subdirectories, filenames in os.walk(resources):
        for filename in sorted(filenames):
            if filename.endswith(".py"):
                yield os.path.join(directory, filename)


def _fat_architectures(path):
    with open(path, "rb") as handle:
        header = handle.read(8)
        if len(header) != 8:
            return set()
        magic, count = struct.unpack(">II", header)
        if magic not in (0xCAFEBABE, 0xCAFEBABF) or count > 16:
            return set()
        architecture_size = 24 if magic == 0xCAFEBABF else 20
        architectures = set()
        for _index in range(count):
            record = handle.read(architecture_size)
            if len(record) != architecture_size:
                return set()
            architectures.add(struct.unpack(">I", record[:4])[0])
        return architectures


def validate(bundle, target):
    errors = []
    checks = []
    bundle = os.path.abspath(bundle)
    if not bundle.endswith(".glyphsReporter") or not os.path.isdir(bundle):
        errors.append("artifact must be an existing .glyphsReporter bundle")
        return errors, checks

    contents = os.path.join(bundle, "Contents")
    resources = os.path.join(contents, "Resources")
    plist_path = os.path.join(contents, "Info.plist")
    loader = os.path.join(contents, "MacOS", "plugin")
    plugin_path = os.path.join(resources, "plugin.py")

    try:
        with open(plist_path, "rb") as handle:
            info = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as error:
        errors.append("invalid Info.plist: {}".format(error))
        info = {}
    else:
        checks.append("valid-plist")
        expected = {
            "CFBundleIdentifier": EXPECTED_ID,
            "CFBundleName": "IconGrid",
            "NSPrincipalClass": EXPECTED_CLASS,
        }
        for key, value in expected.items():
            if info.get(key) != value:
                errors.append("{} must be {!r}".format(key, value))

    principal_found = False
    for path in _python_files(resources):
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = ast.parse(handle.read(), filename=path)
        except (OSError, SyntaxError) as error:
            errors.append("invalid Python source {}: {}".format(path, error))
            continue
        if path == plugin_path:
            principal_found = any(
                isinstance(node, ast.ClassDef) and node.name == EXPECTED_CLASS
                for node in tree.body
            )
    if principal_found:
        checks.extend(["python-syntax", "principal-class"])
    else:
        errors.append("principal class {} not found".format(EXPECTED_CLASS))
    if os.access(plugin_path, os.X_OK):
        checks.append("executable-python-entry-point")
    else:
        errors.append("Python plug-in entry point is not executable")

    try:
        with open(loader, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
    except OSError as error:
        errors.append("missing SDK wrapper: {}".format(error))
    else:
        if digest != EXPECTED_LOADER_SHA256:
            errors.append("SDK wrapper was modified")
        if not os.access(loader, os.X_OK):
            errors.append("SDK wrapper is not executable")
        if not REQUIRED_CPU_TYPES.issubset(_fat_architectures(loader)):
            errors.append("SDK wrapper must contain x86_64 and arm64")
        if not any(item.startswith("SDK wrapper") for item in errors):
            checks.append("unmodified-universal-sdk-wrapper")

    placeholders = ("My Plugin", "____PluginName____", "com.example")
    for path in _python_files(resources):
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        for placeholder in placeholders:
            if placeholder in source:
                errors.append("placeholder {!r} remains in {}".format(placeholder, path))
    if not any("placeholder" in error for error in errors):
        checks.append("no-placeholders")

    checks.append("glyphs-{}-static-contract".format(target))
    return errors, checks


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("bundle")
    parser.add_argument("--target", choices=("3", "4", "both"), default="both")
    arguments = parser.parse_args(argv)
    errors, checks = validate(arguments.bundle, arguments.target)
    result = {
        "ok": not errors,
        "artifact": os.path.abspath(arguments.bundle),
        "target": arguments.target,
        "checks": checks,
        "errors": errors,
        "runtimeTested": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
