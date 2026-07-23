from __future__ import absolute_import

import os
import plistlib
import unittest

from scripts import package as package_script
from scripts import release_check
from tests.support import ROOT


class ReleaseContractTests(unittest.TestCase):
    def test_bundle_and_online_update_metadata_match(self):
        with open(
            os.path.join(ROOT, "IconGrid.glyphsReporter", "Contents", "Info.plist"),
            "rb",
        ) as handle:
            bundle = plistlib.load(handle)
        with open(os.path.join(ROOT, "site", "update", "Info.plist"), "rb") as handle:
            update = plistlib.load(handle)
        for key in ("CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion"):
            self.assertEqual(bundle[key], update[key])
        self.assertEqual(
            bundle["UpdateFeedURL"],
            "https://thierryc.github.io/GlyphsIconGrid/update/Info.plist",
        )

    def test_release_contract_and_checksum(self):
        archive = package_script.main()
        result = release_check.validate(tag="v0.1.0", require_artifacts=True)
        self.assertTrue(result["ok"], result["errors"])
        self.assertTrue(os.path.isfile(archive + ".sha256"))


if __name__ == "__main__":
    unittest.main()
