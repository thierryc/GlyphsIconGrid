from __future__ import absolute_import

import math
import unittest

from tests import support  # noqa: F401
from glyphs_icon_grid.config import (
    DEFAULTS,
    DEFAULT_GRID_COLOR,
    GRID_MODES,
    ORIGINS,
    resolve_config,
)


class ConfigTests(unittest.TestCase):
    def resolve(
        self,
        font=None,
        master=None,
        cap_height=700,
        upm=1000,
        x_height=500,
        ascender=800,
        descender=-200,
    ):
        return resolve_config(
            font_parameters=font or {},
            master_parameters=master or {},
            master_cap_height=cap_height,
            font_upm=upm,
            master_x_height=x_height,
            master_ascender=ascender,
            master_descender=descender,
        )

    def test_defaults_are_complete_and_safe(self):
        config, warnings = self.resolve()
        self.assertEqual(config.columns, 24)
        self.assertEqual(config.rows, 24)
        self.assertIsNone(config.grid_size)
        self.assertEqual(config.grid_mode, "odd")
        self.assertEqual(config.height, 1000.0)
        self.assertEqual(config.width, 1000.0)
        self.assertAlmostEqual(config.width / config.columns, config.height / config.rows)
        self.assertEqual(config.origin, "bottom-center")
        self.assertEqual(config.baseline_offset, 250.0)
        self.assertEqual(config.metric_top, 800.0)
        self.assertEqual(config.metric_bottom, -200.0)
        self.assertEqual(config.padding, 2.0)
        self.assertEqual(config.major_every, 4)
        self.assertEqual(config.rings, 10)
        self.assertEqual(config.spokes, 8)
        self.assertTrue(config.show_keylines)
        self.assertEqual(config.color, DEFAULT_GRID_COLOR)
        self.assertAlmostEqual(config.opacity, 0.28)
        self.assertTrue(config.alignment_highlight)
        self.assertEqual(config.alignment_tolerance, 2.0)
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

    def test_both_grid_modes_are_supported(self):
        self.assertEqual(set(GRID_MODES), {"odd", "even"})

    def test_master_values_override_font_values_partially(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.columns": 32,
                "IconGrid.rows": 20,
                "IconGrid.gridSize": 40,
                "IconGrid.gridMode": "odd",
                "IconGrid.width": 840,
                "IconGrid.origin": "top-right",
                "IconGrid.opacity": 0.4,
                "IconGrid.baselineOffset": 80,
                "IconGrid.alignmentHighlight": False,
                "IconGrid.alignmentTolerance": 8,
            },
            master={
                "IconGrid.rows": 16,
                "IconGrid.gridSize": 72,
                "IconGrid.gridMode": "even",
                "IconGrid.baselineOffset": 100,
                "IconGrid.alignmentHighlight": True,
            },
        )
        self.assertEqual((config.columns, config.rows), (32, 16))
        self.assertEqual(config.grid_size, 72.0)
        self.assertEqual(config.grid_mode, "even")
        self.assertEqual(config.width, 840.0)
        self.assertEqual(config.origin, "top-right")
        self.assertEqual(config.opacity, 0.4)
        self.assertEqual(config.baseline_offset, 100.0)
        self.assertTrue(config.alignment_highlight)
        self.assertEqual(config.alignment_tolerance, 8.0)
        self.assertEqual(warnings, [])

    def test_invalid_grid_mode_falls_through_master_font_and_default(self):
        config, warnings = self.resolve(
            font={"IconGrid.gridMode": "EVEN"},
            master={"IconGrid.gridMode": "center-ish"},
        )
        self.assertEqual(config.grid_mode, "even")
        self.assertEqual(len([item for item in warnings if "gridMode" in item]), 1)

        default_config, default_warnings = self.resolve(
            font={"IconGrid.gridMode": object()}
        )
        self.assertEqual(default_config.grid_mode, "odd")
        self.assertEqual(len([item for item in default_warnings if "gridMode" in item]), 1)

    def test_invalid_alignment_values_fall_through_master_font_and_default(self):
        config, warnings = self.resolve(
            font={
                "IconGrid.alignmentHighlight": "off",
                "IconGrid.alignmentTolerance": 7,
            },
            master={
                "IconGrid.alignmentHighlight": "sometimes",
                "IconGrid.alignmentTolerance": 21,
            },
        )
        self.assertFalse(config.alignment_highlight)
        self.assertEqual(config.alignment_tolerance, 7.0)
        self.assertEqual(len([item for item in warnings if "alignment" in item]), 2)

        default_config, default_warnings = self.resolve(
            font={
                "IconGrid.alignmentHighlight": object(),
                "IconGrid.alignmentTolerance": 0,
            }
        )
        self.assertTrue(default_config.alignment_highlight)
        self.assertEqual(default_config.alignment_tolerance, 2.0)
        self.assertEqual(len([item for item in default_warnings if "alignment" in item]), 2)

    def test_alignment_tolerance_accepts_numeric_strings_at_both_limits(self):
        minimum, warnings = self.resolve(font={"IconGrid.alignmentTolerance": "1"})
        maximum, maximum_warnings = self.resolve(font={"IconGrid.alignmentTolerance": "20"})
        self.assertEqual(minimum.alignment_tolerance, 1.0)
        self.assertEqual(maximum.alignment_tolerance, 20.0)
        self.assertEqual(warnings + maximum_warnings, [])

    def test_invalid_master_value_falls_back_to_valid_font_value(self):
        config, warnings = self.resolve(
            font={"IconGrid.columns": 32},
            master={"IconGrid.columns": "many"},
        )
        self.assertEqual(config.columns, 32)
        self.assertTrue(any("IconGrid.columns" in item for item in warnings))

    def test_invalid_master_grid_size_falls_back_to_valid_font_grid_size(self):
        config, warnings = self.resolve(
            font={"IconGrid.gridSize": 34},
            master={"IconGrid.gridSize": 1},
        )
        self.assertEqual(config.grid_size, 34.0)
        self.assertEqual(len([item for item in warnings if "gridSize" in item]), 1)

    def test_weight_units_can_be_stored_as_exact_master_grid_size(self):
        regular, regular_warnings = self.resolve(
            master={"IconGrid.gridSize": 34}
        )
        bold, bold_warnings = self.resolve(
            master={"IconGrid.gridSize": 72}
        )
        self.assertEqual(regular.grid_size, 34.0)
        self.assertEqual(bold.grid_size, 72.0)
        self.assertEqual(regular_warnings + bold_warnings, [])

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
        self.assertEqual(config.height, 1000.0)
        self.assertEqual(config.width, 1000.0)
        self.assertEqual(config.origin, DEFAULTS["origin"])
        self.assertEqual(config.color, DEFAULT_GRID_COLOR)
        self.assertEqual(config.opacity, DEFAULTS["opacity"])
        self.assertEqual(config.baseline_offset, 250.0)
        self.assertGreaterEqual(len(warnings), 8)

    def test_square_size_falls_back_from_upm_to_cap_height(self):
        upm_config = self.resolve(cap_height=0, upm=2048)[0]
        cap_config = self.resolve(cap_height=720, upm=None)[0]
        hard_config = self.resolve(cap_height=None, upm=None)[0]
        self.assertEqual((upm_config.height, upm_config.width), (2048.0, 2048.0))
        self.assertEqual((cap_config.height, cap_config.width), (720.0, 720.0))
        self.assertEqual((hard_config.height, hard_config.width), (1000.0, 1000.0))

    def test_missing_x_height_keeps_baseline_origin_fallback(self):
        config, warnings = self.resolve(x_height=None)
        self.assertEqual(config.baseline_offset, 0.0)
        self.assertEqual(config.metric_top, 800.0)
        self.assertEqual(config.metric_bottom, -200.0)
        self.assertEqual(warnings, [])

    def test_default_icon_grid_is_a_square_of_square_cells(self):
        for cap_height, upm in ((700, 1000), (720, 1000), (1024, 2048)):
            config, warnings = self.resolve(cap_height=cap_height, upm=upm)
            self.assertEqual(config.width, config.height)
            self.assertEqual(config.columns, config.rows)
            self.assertAlmostEqual(
                config.width / config.columns,
                config.height / config.rows,
            )
            self.assertEqual(warnings, [])

    def test_explicit_column_count_does_not_resize_square_container(self):
        config, warnings = self.resolve(font={"IconGrid.columns": 30})
        self.assertEqual(config.columns, 30)
        self.assertEqual((config.width, config.height), (1000.0, 1000.0))
        self.assertEqual(warnings, [])

    def test_explicit_width_and_columns_can_define_rectangular_cells(self):
        config, warnings = self.resolve(
            font={"IconGrid.columns": 24, "IconGrid.width": 1500}
        )
        self.assertEqual((config.columns, config.width), (24, 1500.0))
        self.assertNotAlmostEqual(config.width / config.columns, config.height / config.rows)
        self.assertEqual(warnings, [])

    def test_glyphs_missing_metric_sentinel_falls_back_to_upm(self):
        config, warnings = self.resolve(
            cap_height=9223372036854775807,
            upm=1000,
        )
        self.assertEqual(config.height, 1000.0)
        self.assertEqual(config.width, 1000.0)
        self.assertEqual(warnings, [])

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
                    "IconGrid.gridSize": value,
                    "IconGrid.gridMode": value,
                    "IconGrid.padding": value,
                    "IconGrid.rings": value,
                    "IconGrid.spokes": value,
                    "IconGrid.opacity": value,
                    "IconGrid.alignmentHighlight": value,
                    "IconGrid.alignmentTolerance": value,
                }
            )
            self.assertGreater(config.columns, 0)
            self.assertGreater(config.rows, 0)
            self.assertTrue(math.isfinite(config.height))
            self.assertTrue(math.isfinite(config.width))
            self.assertTrue(
                config.grid_size is None or math.isfinite(config.grid_size)
            )
            self.assertIn(config.grid_mode, GRID_MODES)
            self.assertTrue(math.isfinite(config.padding))
            self.assertTrue(math.isfinite(config.opacity))
            self.assertIsInstance(config.alignment_highlight, bool)
            self.assertTrue(math.isfinite(config.alignment_tolerance))
            self.assertGreaterEqual(config.alignment_tolerance, 1.0)
            self.assertLessEqual(config.alignment_tolerance, 20.0)


if __name__ == "__main__":
    unittest.main()
