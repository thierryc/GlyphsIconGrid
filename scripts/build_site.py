#!/usr/bin/env python3
"""Assemble the dependency-free GitHub Pages artifact."""

from __future__ import absolute_import, print_function

import os
import shutil


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "site")
SCREENSHOTS = os.path.join(ROOT, "docs", "images")
OUTPUT = os.path.join(ROOT, "build", "site")
SOURCE_IMAGE_PREFIX = "../docs/images/"
PUBLISHED_IMAGE_PREFIX = "assets/images/"
REQUIRED_IMAGES = (
    "icon-grid-overview.png",
    "show-icon-grid-menu.png",
    "default-metrics.png",
    "odd-grid.png",
    "even-grid.png",
    "glyphs-mcp-edit-profile-1.4.png",
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
    shutil.copytree(
        SOURCE,
        OUTPUT,
        ignore=shutil.ignore_patterns("assets"),
    )
    index_path = os.path.join(OUTPUT, "index.html")
    with open(index_path, "r", encoding="utf-8") as index_file:
        index_html = index_file.read()
    index_html = index_html.replace(SOURCE_IMAGE_PREFIX, PUBLISHED_IMAGE_PREFIX)
    with open(index_path, "w", encoding="utf-8") as index_file:
        index_file.write(index_html)
    destination = os.path.join(OUTPUT, "assets", "images")
    os.makedirs(destination, exist_ok=True)
    for name in REQUIRED_IMAGES:
        shutil.copy2(os.path.join(SCREENSHOTS, name), os.path.join(destination, name))
    print(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    main()
