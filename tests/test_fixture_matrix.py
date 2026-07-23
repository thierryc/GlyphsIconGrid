from __future__ import absolute_import

import json
import os
import unittest

from tests.support import ROOT
from glyphs_icon_grid.config import PARAMETER_NAMES, resolve_config
from tests.fixture_parser import parse_fixture


MANIFEST_PATH = os.path.join(ROOT, "tests", "fixtures", "parameter-matrix.json")


class ParameterFixtureMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as handle:
            cls.manifest = json.load(handle)

    def test_manifest_matches_the_public_parameter_contract(self):
        self.assertEqual(tuple(self.manifest["supportedParameters"]), PARAMETER_NAMES)
        covered = set()
        for case in self.manifest["cases"]:
            covered.update(item["name"] for item in case["fontParameters"])
            for records in case["masterParameters"].values():
                covered.update(item["name"] for item in records)
        self.assertEqual(covered, set(PARAMETER_NAMES))

    def test_fixture_files_match_declared_stored_records(self):
        for case in self.manifest["cases"]:
            with self.subTest(case=case["id"]):
                fixture = parse_fixture(
                    os.path.join(ROOT, "tests", "fixtures", case["file"])
                )
                self.assertEqual(fixture["unitsPerEm"], 1000)
                self.assertEqual(fixture["fontParameters"], case["fontParameters"])
                self.assertEqual(
                    {
                        master_id: master["parameters"]
                        for master_id, master in fixture["masters"].items()
                    },
                    case["masterParameters"],
                )

    def test_every_declared_effective_value_uses_the_real_resolver(self):
        for case in self.manifest["cases"]:
            fixture = parse_fixture(
                os.path.join(ROOT, "tests", "fixtures", case["file"])
            )
            all_warnings = []
            for master_id, expected in case["effective"].items():
                config, warnings = resolve_config(
                    fixture["fontParameters"],
                    fixture["masters"][master_id]["parameters"],
                    master_cap_height=700,
                    font_upm=fixture["unitsPerEm"],
                    master_x_height=500,
                    master_ascender=800,
                    master_descender=-200,
                )
                all_warnings.extend(warnings)
                for attribute, value in expected.items():
                    with self.subTest(
                        case=case["id"], master=master_id, attribute=attribute
                    ):
                        self.assertEqual(getattr(config, attribute), value)
            joined = "\n".join(all_warnings)
            for fragment in case["warningsContain"]:
                with self.subTest(case=case["id"], warning=fragment):
                    self.assertIn(fragment, joined)

    def test_mutations_are_guarded_and_exactly_one_case_tests_save_reopen(self):
        save_reopen = 0
        for case in self.manifest["cases"]:
            mutation = case["mutation"]
            self.assertIn(mutation["scope"], ("font", "master"))
            self.assertTrue(mutation["changes"])
            self.assertTrue(set(mutation["changes"]).issubset(PARAMETER_NAMES))
            save_reopen += int(mutation.get("saveReopen", False))
            if mutation.get("expectedBlocker"):
                self.assertEqual(case["id"], "invalid-inactive-duplicates")
        self.assertEqual(save_reopen, 1)


if __name__ == "__main__":
    unittest.main()
