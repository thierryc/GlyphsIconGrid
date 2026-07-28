#!/usr/bin/env python3
"""Build a deterministic release ZIP while preserving bundle permissions."""

from __future__ import absolute_import, print_function

import os
import plistlib
import hashlib
import stat
import zipfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_NAME = "IconGrid.glyphsReporter"
BUNDLE = os.path.join(ROOT, BUNDLE_NAME)
SKILL = os.path.join(ROOT, "skills", "glyphs-mcp-icon-grid")
MACOS_SKILL_INSTALLER = os.path.join(
    ROOT, "scripts", "Install GlyphsIconGrid Skill.command"
)
MACOS_SKILL_INSTALLER_NAME = "Install GlyphsIconGrid Skill.command"
STANDALONE_SKILL_ARCHIVE_NAME = "GlyphsIconGrid-Skill.zip"


def _write_file(archive, path, relative):
    info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
    mode = stat.S_IMODE(os.stat(path).st_mode)
    info.external_attr = (stat.S_IFREG | mode) << 16
    with open(path, "rb") as handle:
        archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED)


def _write_tree(archive, source):
    for directory, subdirectories, filenames in os.walk(source):
        subdirectories[:] = sorted(
            name for name in subdirectories if name != "__pycache__"
        )
        for filename in sorted(filenames):
            if filename.endswith((".pyc", ".pyo")):
                continue
            path = os.path.join(directory, filename)
            _write_file(archive, path, os.path.relpath(path, ROOT))


def _write_checksum(output):
    with open(output, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    checksum = output + ".sha256"
    with open(checksum, "w", encoding="ascii", newline="\n") as handle:
        handle.write("{}  {}\n".format(digest, os.path.basename(output)))
    return checksum


def build_standalone_skill(output_directory):
    output = os.path.join(output_directory, STANDALONE_SKILL_ARCHIVE_NAME)
    if os.path.exists(output):
        os.unlink(output)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_file(
            archive,
            MACOS_SKILL_INSTALLER,
            MACOS_SKILL_INSTALLER_NAME,
        )
        _write_tree(archive, SKILL)
        for filename in ("LICENSE", "NOTICE"):
            path = os.path.join(ROOT, filename)
            _write_file(archive, path, filename)
    _write_checksum(output)
    return output


def main():
    with open(os.path.join(BUNDLE, "Contents", "Info.plist"), "rb") as handle:
        version = plistlib.load(handle)["CFBundleShortVersionString"]
    output_directory = os.path.join(ROOT, "dist")
    os.makedirs(output_directory, exist_ok=True)
    output = os.path.join(output_directory, "GlyphsIconGrid-{}.zip".format(version))
    if os.path.exists(output):
        os.unlink(output)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        _write_tree(archive, BUNDLE)
        _write_tree(archive, SKILL)
        _write_file(
            archive,
            MACOS_SKILL_INSTALLER,
            MACOS_SKILL_INSTALLER_NAME,
        )
        for filename in ("LICENSE", "NOTICE"):
            path = os.path.join(ROOT, filename)
            _write_file(archive, path, filename)
    _write_checksum(output)
    standalone_skill = build_standalone_skill(output_directory)
    print(output)
    print(standalone_skill)
    return output


if __name__ == "__main__":
    main()
