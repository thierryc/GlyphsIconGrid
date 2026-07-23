#!/usr/bin/env python3
"""Install the portable GlyphsIconGrid skill for a supported local AI client."""

from __future__ import absolute_import, print_function

import argparse
import json
import os
import shutil
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE = os.path.join(ROOT, "skills", "glyphs-mcp-icon-grid")
SKILL_NAME = "glyphs-mcp-icon-grid"
USER_ROOTS = {
    "codex": os.path.join(".agents", "skills"),
    "claude": os.path.join(".claude", "skills"),
    "gemini": os.path.join(".agents", "skills"),
    "cursor": os.path.join(".agents", "skills"),
}
PROJECT_ROOTS = {
    "codex": os.path.join(".agents", "skills"),
    "claude": os.path.join(".claude", "skills"),
    "gemini": os.path.join(".agents", "skills"),
    "cursor": os.path.join(".agents", "skills"),
}


def destination_for(client, scope, home=None, project_root=None):
    if scope == "user":
        base = os.path.abspath(os.path.expanduser(home or "~"))
        relative = USER_ROOTS[client]
    else:
        base = os.path.abspath(project_root or os.getcwd())
        relative = PROJECT_ROOTS[client]
    return os.path.join(base, relative, SKILL_NAME)


def install(client, scope, home=None, project_root=None, dry_run=False, force=False):
    destination = destination_for(client, scope, home=home, project_root=project_root)
    result = {
        "client": client,
        "scope": scope,
        "source": SOURCE,
        "destination": destination,
        "dryRun": bool(dry_run),
        "force": bool(force),
        "installed": False,
    }
    if not os.path.isfile(os.path.join(SOURCE, "SKILL.md")):
        raise RuntimeError("canonical skill is incomplete: {}".format(SOURCE))
    if os.path.lexists(destination) and not force:
        raise FileExistsError(
            "{} already exists; inspect it, then rerun with --force to replace it".format(
                destination
            )
        )
    if dry_run:
        result["action"] = "replace" if os.path.lexists(destination) else "create"
        return result

    parent = os.path.dirname(destination)
    os.makedirs(parent, exist_ok=True)
    if os.path.lexists(destination):
        if os.path.isdir(destination) and not os.path.islink(destination):
            shutil.rmtree(destination)
        else:
            os.unlink(destination)
    shutil.copytree(SOURCE, destination)
    result["action"] = "installed"
    result["installed"] = True
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Install the Glyphs MCP Icon Grid skill without editing MCP client settings."
    )
    parser.add_argument("--client", required=True, choices=sorted(USER_ROOTS))
    parser.add_argument("--scope", required=True, choices=("user", "project"))
    parser.add_argument("--project-root")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args(argv)
    if arguments.project_root and arguments.scope != "project":
        parser.error("--project-root is valid only with --scope project")
    try:
        result = install(
            arguments.client,
            arguments.scope,
            project_root=arguments.project_root,
            dry_run=arguments.dry_run,
            force=arguments.force,
        )
    except (RuntimeError, FileExistsError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(dict(result, ok=True), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
