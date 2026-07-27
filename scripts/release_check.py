#!/usr/bin/env python3
"""Validate the public version contract before tagging a release."""

from __future__ import absolute_import, print_function

import argparse
import hashlib
import json
import os
import plistlib
import re
import stat
import sys
import zipfile


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUNDLE_PLIST = os.path.join(ROOT, "IconGrid.glyphsReporter", "Contents", "Info.plist")
UPDATE_PLIST = os.path.join(ROOT, "site", "update", "Info.plist")
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
README = os.path.join(ROOT, "README.md")


def _load_plist(path):
    with open(path, "rb") as handle:
        return plistlib.load(handle)


def validate(tag=None, require_artifacts=False):
    errors = []
    checks = []
    bundle = _load_plist(BUNDLE_PLIST)
    update = _load_plist(UPDATE_PLIST)
    version = str(bundle.get("CFBundleShortVersionString", ""))
    build = str(bundle.get("CFBundleVersion", ""))
    expected_tag = "v" + version
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        errors.append("CFBundleShortVersionString must be semantic x.y.z")
    if not build.isdigit() or int(build) < 1:
        errors.append("CFBundleVersion must be a positive integer")
    for key in ("CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion"):
        if str(update.get(key, "")) != str(bundle.get(key, "")):
            errors.append("update plist {} does not match bundle".format(key))
    if bundle.get("productPageURL") != "https://thierryc.github.io/GlyphsIconGrid/":
        errors.append("productPageURL is not the public Pages URL")
    if bundle.get("UpdateFeedURL") != "https://thierryc.github.io/GlyphsIconGrid/update/Info.plist":
        errors.append("UpdateFeedURL is not the public Pages update plist")
    if tag and tag != expected_tag:
        errors.append("tag {} does not match {}".format(tag, expected_tag))

    with open(CHANGELOG, "r", encoding="utf-8") as handle:
        changelog = handle.read()
    with open(README, "r", encoding="utf-8") as handle:
        readme = handle.read()
    if version not in changelog:
        errors.append("CHANGELOG.md has no {} section".format(version))
    if "84" not in readme or "135" not in readme or "odd" not in readme:
        errors.append("README.md is missing the recommended grid contract")
    release_notes = os.path.join(ROOT, "docs", "releases", "{}.md".format(version))
    if not os.path.isfile(release_notes):
        errors.append("missing release notes {}".format(os.path.relpath(release_notes, ROOT)))

    archive = os.path.join(ROOT, "dist", "GlyphsIconGrid-{}.zip".format(version))
    checksum_path = archive + ".sha256"
    if require_artifacts:
        if not os.path.isfile(archive):
            errors.append("missing release archive")
        if not os.path.isfile(checksum_path):
            errors.append("missing checksum file")
        if os.path.isfile(archive) and os.path.isfile(checksum_path):
            with open(archive, "rb") as handle:
                digest = hashlib.sha256(handle.read()).hexdigest()
            with open(checksum_path, "r", encoding="ascii") as handle:
                recorded = handle.read().split()[0]
            if digest != recorded:
                errors.append("release checksum does not match archive")
        if os.path.isfile(archive):
            required_members = {
                "IconGrid.glyphsReporter/Contents/Info.plist",
                "Install GlyphsIconGrid Skill.command",
                "skills/glyphs-mcp-icon-grid/SKILL.md",
                "skills/glyphs-mcp-icon-grid/agents/openai.yaml",
                "skills/glyphs-mcp-icon-grid/references/parameters.md",
            }
            with zipfile.ZipFile(archive, "r") as release_zip:
                names = set(release_zip.namelist())
                missing = sorted(required_members - names)
                if missing:
                    errors.append(
                        "release archive is missing {}".format(", ".join(missing))
                    )
                if "Install GlyphsIconGrid Skill.command" in names:
                    installer = release_zip.getinfo(
                        "Install GlyphsIconGrid Skill.command"
                    )
                    mode = stat.S_IMODE(installer.external_attr >> 16)
                    if mode != 0o755:
                        errors.append("Mac skill installer is not executable")

    checks.extend(
        (
            "bundle-version",
            "online-update-plist",
            "release-notes",
            "readme-contract",
        )
    )
    if require_artifacts:
        checks.extend(("release-artifacts", "bundled-skill-installer"))
    return {
        "ok": not errors,
        "version": version,
        "build": build,
        "expectedTag": expected_tag,
        "checks": checks,
        "errors": errors,
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag")
    parser.add_argument("--require-artifacts", action="store_true")
    arguments = parser.parse_args(argv)
    result = validate(tag=arguments.tag, require_artifacts=arguments.require_artifacts)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
