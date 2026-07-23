#!/usr/bin/env python3
"""Assemble the dependency-free GitHub Pages artifact."""

from __future__ import absolute_import, print_function

import os
import shutil


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "site")
SCREENSHOTS = os.path.join(ROOT, "docs", "images")
OUTPUT = os.path.join(ROOT, "build", "site")
REQUIRED_IMAGES = (
    "icon-grid-overview.png",
    "show-icon-grid-menu.png",
    "font-info-grid-size.png",
    "regular-bold-grid.png",
    "odd-even-grid.png",
    "glyphs-mcp-edit-profile.png",
)


def main():
    missing = [
        name for name in REQUIRED_IMAGES
        if not os.path.isfile(os.path.join(SCREENSHOTS, name))
    ]
    if missing:
        raise RuntimeError("missing site images: {}".format(", ".join(missing)))
    if os.path.isdir(OUTPUT):
        shutil.rmtree(OUTPUT)
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    shutil.copytree(SOURCE, OUTPUT)
    destination = os.path.join(OUTPUT, "assets", "images")
    os.makedirs(destination, exist_ok=True)
    for name in REQUIRED_IMAGES:
        shutil.copy2(os.path.join(SCREENSHOTS, name), os.path.join(destination, name))
    print(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    main()
