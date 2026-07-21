from __future__ import absolute_import

import math
import unittest

from tests import support  # noqa: F401
from icon_grid.config import DEFAULTS, ORIGINS, resolve_config


class ConfigTests(unittest.TestCase):
    def resolve(self, font=None, master=None, cap_height=700, upm=1000):
        return resolve_config(
            font_parameters=font or {},
            master_parameters=master or {},
            master_cap_height=cap_height,
            font_upm=upm,
        )

    def test_defaults_are_complete_and_safe(self):
        config, warnings = self.resolve()
        self.assertEqual(config.columns, 24)
        self.assertEqual(config.rows, 24)
        self.assertEqual(config.height, 700.0)
        self.assertEqual(config.width, 1500.0)
        self.assertEqual(config.origin, "bottom-left")
        self.assertEqual(config.baseline_offset, 0.0)
        self.assertEqual(config.padding, 2.0)
        self.assertEqual(config.major_every, 4)
        self.assertEqual(config.rings, 10)
        self.assertEqual(config.spokes, 8)
        self.assertTrue(config.show_keylines)
        self.assertEqual(config.color, "accent")
        self.assertAlmostEqual(config.opacity, 0.28)
        self.assertEqual(warnings, [])

    def test_all_nine_origins_are_supported(self):
        self.assertEqual(
            set(ORIGINS),
            {
                "bottom-left", "bottom-center", "bottom-right",
                "center-left", "center", "center-right",
                "top-left", "top-center", "top-right",
            },
        )

    def test_master_values_override_font_values_partially(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.columns": 32,
                "IconGrid.rows": 20,
                "IconGrid.width": 840,
                "IconGrid.origin": "top-right",
                "IconGrid.opacity": 0.4,
                "IconGrid.baselineOffset": 80,
            },
            master={"IconGrid.rows": 16, "IconGrid.baselineOffset": 100},
        )
        self.assertEqual((config.columns, config.rows), (32, 16))
        self.assertEqual(config.width, 840.0)
        self.assertEqual(config.origin, "top-right")
        self.assertEqual(config.opacity, 0.4)
        self.assertEqual(config.baseline_offset, 100.0)
        self.assertEqual(warnings, [])

    def test_invalid_master_value_falls_back_to_valid_font_value(self):
        config, warnings = self.resolve(
            font={"IconGrid.columns": 32},
            master={"IconGrid.columns": "many"},
        )
        self.assertEqual(config.columns, 32)
        self.assertTrue(any("IconGrid.columns" in item for item in warnings))

    def test_invalid_numbers_unknown_origin_and_malformed_color_fall_back(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.columns": 0,
                "IconGrid.rows": 257,
                "IconGrid.height": float("nan"),
                "IconGrid.width": float("inf"),
                "IconGrid.origin": "middle-ish",
                "IconGrid.color": "blue",
                "IconGrid.opacity": float("inf"),
                "IconGrid.baselineOffset": float("nan"),
            }
        )
        self.assertEqual(config.columns, DEFAULTS["columns"])
        self.assertEqual(config.rows, DEFAULTS["rows"])
        self.assertEqual(config.height, 700.0)
        self.assertEqual(config.width, 1500.0)
        self.assertEqual(config.origin, DEFAULTS["origin"])
        self.assertEqual(config.color, "accent")
        self.assertEqual(config.opacity, DEFAULTS["opacity"])
        self.assertEqual(config.baseline_offset, 0.0)
        self.assertGreaterEqual(len(warnings), 8)

    def test_height_falls_back_from_cap_height_to_upm_to_1000(self):
        upm_config = self.resolve(cap_height=0, upm=2048)[0]
        hard_config = self.resolve(cap_height=None, upm=None)[0]
        self.assertEqual((upm_config.height, upm_config.width), (2048.0, 3072.0))
        self.assertEqual((hard_config.height, hard_config.width), (1000.0, 1500.0))

    def test_padding_and_opacity_are_clamped(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.columns": 10,
                "IconGrid.rows": 8,
                "IconGrid.padding": 100,
                "IconGrid.opacity": -0.5,
            }
        )
        self.assertEqual(config.padding, 3.5)
        self.assertEqual(config.opacity, 0.0)
        self.assertTrue(any("clamped" in item for item in warnings))

    def test_boolean_color_and_numeric_strings_are_supported(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.columns": "32",
                "IconGrid.height": "900.5",
                "IconGrid.width": "1200",
                "IconGrid.showKeylines": "off",
                "IconGrid.color": "#3366CC",
                "IconGrid.rings": "0",
                "IconGrid.spokes": 0,
            }
        )
        self.assertEqual(config.columns, 32)
        self.assertEqual(config.height, 900.5)
        self.assertEqual(config.width, 1200.0)
        self.assertFalse(config.show_keylines)
        self.assertEqual(config.color, (0.2, 0.4, 0.8))
        self.assertEqual(config.rings, 0)
        self.assertEqual(config.spokes, 0)
        self.assertEqual(warnings, [])

    def test_semantic_macos_colors_are_supported(self):
        for name in ("accent", "grid", "label", "separator"):
            config, warnings = self.resolve(font={"IconGrid.color": name.upper()})
            self.assertEqual(config.color, name)
            self.assertEqual(warnings, [])

    def test_disabled_entries_do_not_override_active_values(self):
        config, warnings = resolve_config(
            font_parameters=[
                {"name": "IconGrid.columns", "value": 30, "active": True},
                {"name": "IconGrid.rows", "value": 40, "active": False},
            ],
            master_parameters=[],
            master_cap_height=700,
            font_upm=1000,
        )
        self.assertEqual(config.columns, 30)
        self.assertEqual(config.rows, 24)
        self.assertEqual(warnings, [])

    def test_duplicate_active_entries_use_last_value_and_warn(self):
        config, warnings = resolve_config(
            font_parameters=[
                ("IconGrid.columns", 16, True),
                ("IconGrid.columns", 20, True),
            ],
            master_parameters=[],
            master_cap_height=700,
            font_upm=1000,
        )
        self.assertEqual(config.columns, 20)
        self.assertTrue(any("duplicate" in item.lower() for item in warnings))

    def test_fuzzed_bad_values_never_create_non_finite_configuration(self):
        bad_values = [None, "", object(), [], {}, math.nan, math.inf, -math.inf]
        for value in bad_values:
            config, _warnings = self.resolve(
                font={
                    "IconGrid.columns": value,
                    "IconGrid.rows": value,
                    "IconGrid.height": value,
                    "IconGrid.width": value,
                    "IconGrid.padding": value,
                    "IconGrid.rings": value,
                    "IconGrid.spokes": value,
                    "IconGrid.opacity": value,
                }
            )
            self.assertGreater(config.columns, 0)
            self.assertGreater(config.rows, 0)
            self.assertTrue(math.isfinite(config.height))
            self.assertTrue(math.isfinite(config.width))
            self.assertTrue(math.isfinite(config.padding))
            self.assertTrue(math.isfinite(config.opacity))


if __name__ == "__main__":
    unittest.main()
