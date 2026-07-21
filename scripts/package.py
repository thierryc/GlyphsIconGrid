#!/usr/bin/env python3
"""Build a deterministic release ZIP while preserving bundle permissions."""

from __future__ import absolute_import, print_function

import os
import plistlib
import stat
import zipfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_NAME = "IconGrid.glyphsReporter"
BUNDLE = os.path.join(ROOT, BUNDLE_NAME)


def main():
    with open(os.path.join(BUNDLE, "Contents", "Info.plist"), "rb") as handle:
        version = plistlib.load(handle)["CFBundleShortVersionString"]
    output_directory = os.path.join(ROOT, "dist")
    os.makedirs(output_directory, exist_ok=True)
    output = os.path.join(output_directory, "GlyphsIconGrid-{}.zip".format(version))
    if os.path.exists(output):
        os.unlink(output)
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for directory, subdirectories, filenames in os.walk(BUNDLE):
            subdirectories[:] = sorted(
                name for name in subdirectories if name != "__pycache__"
            )
            for filename in sorted(filenames):
                if filename.endswith((".pyc", ".pyo")):
                    continue
                path = os.path.join(directory, filename)
                relative = os.path.relpath(path, ROOT)
                info = zipfile.ZipInfo(relative, date_time=(2026, 1, 1, 0, 0, 0))
                mode = stat.S_IMODE(os.stat(path).st_mode)
                info.external_attr = (stat.S_IFREG | mode) << 16
                with open(path, "rb") as handle:
                    archive.writestr(info, handle.read(), compress_type=zipfile.ZIP_DEFLATED)
    print(output)
    return output


if __name__ == "__main__":
    main()
