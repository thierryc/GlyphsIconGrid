from __future__ import absolute_import

import os
import tempfile
import unittest

from scripts import install_skill


class SkillInstallerTests(unittest.TestCase):
    def test_user_destinations_are_client_appropriate(self):
        with tempfile.TemporaryDirectory() as home:
            self.assertIn(
                os.path.join(".agents", "skills"),
                install_skill.destination_for("codex", "user", home=home),
            )
            self.assertIn(
                os.path.join(".claude", "skills"),
                install_skill.destination_for("claude", "user", home=home),
            )

    def test_dry_run_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as home:
            result = install_skill.install("cursor", "user", home=home, dry_run=True)
            self.assertEqual(result["action"], "create")
            self.assertFalse(os.path.exists(result["destination"]))

    def test_install_copies_complete_skill_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as project:
            result = install_skill.install(
                "claude", "project", project_root=project
            )
            self.assertTrue(result["installed"])
            self.assertTrue(os.path.isfile(os.path.join(result["destination"], "SKILL.md")))
            self.assertTrue(
                os.path.isfile(
                    os.path.join(
                        result["destination"], "references", "release-verification.md"
                    )
                )
            )
            with self.assertRaises(FileExistsError):
                install_skill.install("claude", "project", project_root=project)

    def test_force_replaces_only_the_exact_destination(self):
        with tempfile.TemporaryDirectory() as project:
            result = install_skill.install("codex", "project", project_root=project)
            marker = os.path.join(result["destination"], "local-marker")
            with open(marker, "w", encoding="utf-8") as handle:
                handle.write("replace me")
            replaced = install_skill.install(
                "codex", "project", project_root=project, force=True
            )
            self.assertTrue(replaced["installed"])
            self.assertFalse(os.path.exists(marker))


if __name__ == "__main__":
    unittest.main()
