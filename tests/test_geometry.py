from __future__ import absolute_import

import math
import unittest

from tests import support  # noqa: F401
from glyphs_icon_grid.config import resolve_config
from glyphs_icon_grid.geometry import (
    GuideRef,
    Line,
    build_geometry,
    canvas_for_origin,
    hit_test_guides,
    line_width_for_scale,
    snapshot,
)


class GeometryTests(unittest.TestCase):
    def config(self, **values):
        parameters = {"IconGrid." + key: value for key, value in values.items()}
        return resolve_config(parameters, {}, None, 1000)[0]

    def test_all_origins_have_exact_bounds(self):
        expected = {
            "bottom-left": (0, 0, 800, 600),
            "bottom-center": (100, 0, 900, 600),
            "bottom-right": (200, 0, 1000, 600),
            "center-left": (0, -300, 800, 300),
            "center": (100, -300, 900, 300),
            "center-right": (200, -300, 1000, 300),
            "top-left": (0, -600, 800, 0),
            "top-center": (100, -600, 900, 0),
            "top-right": (200, -600, 1000, 0),
        }
        for origin, bounds in expected.items():
            canvas = canvas_for_origin(800, 600, origin, anchor_width=1000)
            self.assertEqual(canvas.as_tuple(), bounds, origin)

    def test_fixed_grid_does_not_stretch_with_glyph_advance(self):
        config = self.config(width=800, height=800, origin="bottom-center")
        narrow = build_geometry(800, config)
        wide = build_geometry(1200, config)
        self.assertEqual(narrow.canvas.as_tuple(), (0.0, 0.0, 800.0, 800.0))
        self.assertEqual(wide.canvas.as_tuple(), (200.0, 0.0, 1000.0, 800.0))
        self.assertEqual(narrow.canvas.width, wide.canvas.width)
        self.assertEqual(narrow.canvas.height, wide.canvas.height)
        self.assertEqual(narrow.live_radius, wide.live_radius)

    def test_default_origin_centers_canvas_horizontally_on_advance(self):
        geometry = build_geometry(1000, self.config(width=800, height=600))
        self.assertEqual(geometry.canvas.as_tuple(), (100.0, 0.0, 900.0, 600.0))

    def test_default_odd_grid_cadence_is_symmetric_from_canvas_center(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                columns=10,
                rows=8,
                majorEvery=2,
                origin="bottom-left",
            ),
        )
        major_x = sorted(
            line.x1
            for line in geometry.major_lines
            if line.x1 == line.x2 and geometry.canvas.xmin < line.x1 < geometry.canvas.xmax
        )
        self.assertEqual(major_x, [150.0, 350.0, 650.0, 850.0])
        self.assertEqual(geometry.axis_lines, [])
        verticals = sorted(
            line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
        )
        self.assertIn(450.0, verticals)
        self.assertIn(550.0, verticals)
        self.assertNotIn(500.0, verticals)

    def test_even_grid_mode_puts_grid_lines_on_both_center_axes(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=800,
                columns=10,
                rows=8,
                majorEvery=2,
                origin="bottom-left",
                gridMode="even",
            ),
        )
        self.assertIn(
            Line(500.0, geometry.grid_bounds.ymin, 500.0, geometry.grid_bounds.ymax),
            geometry.axis_lines,
        )
        self.assertIn(
            Line(geometry.grid_bounds.xmin, 400.0, geometry.grid_bounds.xmax, 400.0),
            geometry.axis_lines,
        )
        major_x = sorted(
            line.x1
            for line in geometry.major_lines
            if line.x1 == line.x2 and geometry.canvas.xmin < line.x1 < geometry.canvas.xmax
        )
        self.assertEqual(major_x, [100.0, 300.0, 700.0, 900.0])

    def test_every_grid_line_is_axis_aligned_and_spans_the_overflow_bounds(self):
        geometry = build_geometry(
            900, self.config(width=900, columns=9, rows=7, height=700, origin="top-right")
        )
        for line in geometry.all_grid_lines():
            if line.x1 == line.x2:
                self.assertEqual(
                    (line.y1, line.y2),
                    (geometry.grid_bounds.ymin, geometry.grid_bounds.ymax),
                )
            elif line.y1 == line.y2:
                self.assertEqual(
                    (line.x1, line.x2),
                    (geometry.grid_bounds.xmin, geometry.grid_bounds.xmax),
                )
            else:
                self.fail("Grid line is diagonal: {!r}".format(line))

    def test_background_grid_overflows_canvas_by_one_square_cell(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=800,
                columns=10,
                rows=8,
                origin="bottom-left",
            ),
        )
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, 0.0, 1000.0, 800.0))
        self.assertEqual(geometry.grid_bounds.as_tuple(), (-100.0, -100.0, 1100.0, 900.0))
        vertical_positions = {
            line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
        }
        horizontal_positions = {
            line.y1 for line in geometry.all_grid_lines() if line.y1 == line.y2
        }
        self.assertEqual((min(vertical_positions), max(vertical_positions)), (-50.0, 1050.0))
        self.assertEqual((min(horizontal_positions), max(horizontal_positions)), (-50.0, 850.0))

    def test_default_square_centers_in_x_height_and_crosses_all_font_metrics(self):
        config = resolve_config(
            {},
            {},
            master_cap_height=700,
            font_upm=1000,
            master_x_height=500,
            master_ascender=800,
            master_descender=-200,
        )[0]
        geometry = build_geometry(1000, config)
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, -250.0, 1000.0, 750.0))
        self.assertEqual(geometry.center, (500.0, 250.0))
        self.assertTrue(all(ring.cy == 250.0 for ring in geometry.rings))
        self.assertTrue(all(spoke.y1 == 250.0 for spoke in geometry.spokes))
        self.assertTrue(
            all(keyline.y + keyline.height / 2.0 == 250.0 for keyline in geometry.keylines)
        )
        self.assertAlmostEqual(geometry.grid_bounds.width, geometry.grid_bounds.height)
        for metric in (-200.0, 500.0, 700.0, 800.0):
            self.assertLessEqual(geometry.grid_bounds.ymin, metric)
            self.assertGreaterEqual(geometry.grid_bounds.ymax, metric)
        cell_size = 1000.0 / 24.0
        self.assertGreaterEqual(geometry.grid_bounds.ymax, 800.0 + cell_size)
        self.assertLessEqual(geometry.grid_bounds.ymin, -200.0 - cell_size)
        self.assertAlmostEqual(geometry.grid_bounds.xmin, -125.0)
        self.assertAlmostEqual(geometry.grid_bounds.ymin, -375.0)
        self.assertAlmostEqual(geometry.grid_bounds.xmax, 1125.0)
        self.assertAlmostEqual(geometry.grid_bounds.ymax, 875.0)

    def test_metric_overflow_is_capped_to_keep_background_compact(self):
        config = resolve_config(
            {},
            {},
            master_cap_height=700,
            font_upm=1000,
            master_x_height=500,
            master_ascender=5000,
            master_descender=-5000,
        )[0]
        geometry = build_geometry(1000, config)
        cell_size = 1000.0 / 24.0
        self.assertAlmostEqual(geometry.grid_bounds.xmin, -6.0 * cell_size)
        self.assertAlmostEqual(geometry.grid_bounds.xmax, 1000.0 + 6.0 * cell_size)
        self.assertAlmostEqual(geometry.grid_bounds.width, 1500.0)
        self.assertAlmostEqual(geometry.grid_bounds.height, 1500.0)

    def test_baseline_offset_moves_canvas_without_changing_odd_center_phase(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=800,
                rows=8,
                origin="bottom-left",
                baselineOffset=200,
            ),
        )
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, -200.0, 1000.0, 600.0))
        self.assertEqual(geometry.center, (500.0, 200.0))
        horizontal_positions = {
            line.y1 for line in geometry.all_grid_lines() if line.y1 == line.y2
        }
        self.assertEqual(geometry.axis_lines, [])
        self.assertIn(150.0, horizontal_positions)
        self.assertIn(250.0, horizontal_positions)
        self.assertNotIn(200.0, horizontal_positions)
        self.assertTrue(all(circle.cy == 200.0 for circle in geometry.rings))

    def test_centered_odd_grid_centers_one_cell_on_both_axes(self):
        geometry = build_geometry(
            900, self.config(width=900, columns=9, rows=7, height=700, origin="center")
        )
        verticals = sorted(
            line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
        )
        self.assertEqual(verticals[0], -100.0)
        self.assertEqual(verticals[-1], 1000.0)
        self.assertIn(400.0, verticals)
        self.assertIn(500.0, verticals)
        self.assertNotIn(450.0, verticals)
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, -350.0, 900.0, 350.0))

    def test_live_area_padding_is_in_grid_cells(self):
        geometry = build_geometry(
            1200,
            self.config(
                width=1200,
                columns=24,
                rows=12,
                height=600,
                padding=2,
                origin="bottom-left",
            ),
        )
        self.assertEqual(geometry.live_area.as_tuple(), (100.0, 100.0, 1100.0, 500.0))

    def test_master_grid_size_controls_square_cells_and_ring_gaps_exactly(self):
        for spacing, expected_ring_count in ((34.0, 12), (72.0, 4)):
            config = resolve_config(
                {},
                {
                    "IconGrid.columns": 1,
                    "IconGrid.rows": 1,
                    "IconGrid.gridSize": spacing,
                    "IconGrid.rings": 1,
                },
                master_cap_height=700,
                font_upm=1000,
                master_x_height=500,
            )[0]
            geometry = build_geometry(1000, config)
            verticals = sorted(
                line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
            )
            horizontals = sorted(
                line.y1 for line in geometry.all_grid_lines() if line.y1 == line.y2
            )
            self.assertTrue(
                all(abs((right - left) - spacing) < 1e-9 for left, right in zip(verticals, verticals[1:]))
            )
            self.assertTrue(
                all(abs((top - bottom) - spacing) < 1e-9 for bottom, top in zip(horizontals, horizontals[1:]))
            )
            self.assertEqual(len(geometry.rings), expected_ring_count)
            radii = [0.0] + [ring.radius for ring in geometry.rings]
            self.assertTrue(
                all(abs((outer - inner) - spacing) < 1e-9 for inner, outer in zip(radii, radii[1:]))
            )

    def test_rings_are_true_circles_centered_in_rectangular_canvas(self):
        geometry = build_geometry(
            1200, self.config(width=1200, height=800, rings=4, origin="top-right")
        )
        self.assertEqual(geometry.center, (600.0, -400.0))
        expected_step = (800.0 - 2 * (2 * 800.0 / 24.0)) / 2.0 / 4.0
        for circle, expected_radius in zip(geometry.rings, [expected_step * i for i in range(1, 5)]):
            self.assertAlmostEqual(circle.radius, expected_radius)
        for circle in geometry.rings:
            self.assertEqual(circle.cx, 600.0)
            self.assertEqual(circle.cy, -400.0)

    def test_spokes_are_evenly_spaced_on_outer_live_circle(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                spokes=8,
                rings=0,
                origin="bottom-left",
            ),
        )
        self.assertEqual(len(geometry.spokes), 8)
        endpoints = {(round(line.x2, 6), round(line.y2, 6)) for line in geometry.spokes}
        self.assertIn((916.666667, 500.0), endpoints)
        self.assertIn((500.0, 83.333333), endpoints)
        for line in geometry.spokes:
            radius = math.hypot(line.x2 - geometry.center[0], line.y2 - geometry.center[1])
            self.assertAlmostEqual(radius, geometry.live_radius)

    def test_material_keyline_proportions(self):
        geometry = build_geometry(
            1000, self.config(width=1000, height=1000, showKeylines=True)
        )
        keylines = {shape.name: shape for shape in geometry.keylines}
        diameter = geometry.live_radius * 2
        self.assertAlmostEqual(keylines["circle"].width, diameter)
        self.assertAlmostEqual(keylines["square"].width, diameter * 0.9)
        self.assertAlmostEqual(keylines["portrait"].width, diameter * 0.8)
        self.assertAlmostEqual(keylines["portrait"].height, diameter)
        self.assertAlmostEqual(keylines["landscape"].width, diameter)
        self.assertAlmostEqual(keylines["landscape"].height, diameter * 0.8)

    def test_keylines_can_be_disabled(self):
        geometry = build_geometry(1000, self.config(showKeylines=False))
        self.assertEqual(geometry.keylines, [])

    def test_line_width_is_constant_in_screen_pixels(self):
        self.assertAlmostEqual(line_width_for_scale(1.0, 1.0), 1.0)
        self.assertAlmostEqual(line_width_for_scale(1.0, 2.0), 0.5)
        self.assertAlmostEqual(line_width_for_scale(1.0, 0.25), 4.0)
        self.assertTrue(math.isfinite(line_width_for_scale(1.0, 0)))

    def test_hit_testing_includes_every_visible_guide_kind(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                columns=10,
                rows=10,
                majorEvery=2,
                padding=1,
                rings=4,
                spokes=8,
                showKeylines=True,
                origin="bottom-left",
                gridMode="even",
            ),
        )
        probes = {
            "minor": (400.0, 750.0),
            "major": (300.0, 750.0),
            "axis": (500.0, 750.0),
            "frame": (500.0, 1000.0),
            "ring": (900.0, 500.0),
            "spoke": (750.0, 500.0),
            "keyline": (500.0, 860.0),
        }
        for kind, point in probes.items():
            hits = hit_test_guides(geometry, point, 0.001)
            self.assertTrue(any(hit.kind == kind for hit in hits), (kind, hits))

    def test_hit_testing_highlights_all_crossing_guides(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                columns=10,
                rows=10,
                majorEvery=2,
                padding=1,
                rings=0,
                spokes=0,
                showKeylines=False,
                origin="bottom-left",
                gridMode="even",
            ),
        )
        hits = hit_test_guides(geometry, (300.0, 300.0), 0.001)
        major_hits = [hit for hit in hits if hit.kind == "major"]
        self.assertEqual(len(major_hits), 2)

    def test_hit_testing_deduplicates_coincident_ring_and_keyline_circle(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                columns=10,
                rows=10,
                padding=1,
                rings=4,
                spokes=0,
                showKeylines=True,
                origin="bottom-left",
            ),
        )
        hits = hit_test_guides(geometry, (900.0, 500.0), 0.001)
        self.assertIn(GuideRef("ring", 3), hits)
        self.assertNotIn(GuideRef("keyline", 0), hits)

    def test_hit_testing_uses_bounded_segments_and_rect_perimeters(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                columns=1,
                rows=1,
                padding=0,
                rings=0,
                spokes=1,
                showKeylines=False,
                origin="bottom-left",
            ),
        )
        self.assertEqual(hit_test_guides(geometry, (1100.0, 500.0), 5.0), ())
        frame_hits = hit_test_guides(geometry, (1002.0, 1002.0), 3.0)
        self.assertIn(GuideRef("frame", 0), frame_hits)
        self.assertEqual(hit_test_guides(geometry, (1004.0, 1004.0), 3.0), ())

    def test_hit_tolerance_can_be_converted_from_constant_screen_points(self):
        geometry = build_geometry(
            1000,
            self.config(
                width=1000,
                height=1000,
                columns=10,
                rows=10,
                rings=0,
                spokes=0,
                showKeylines=False,
                origin="bottom-left",
                gridMode="even",
            ),
        )
        point = (204.0, 750.0)
        self.assertTrue(
            any(hit.kind == "minor" for hit in hit_test_guides(geometry, point, 5.0 / 1.0))
        )
        self.assertFalse(
            any(hit.kind == "minor" for hit in hit_test_guides(geometry, point, 5.0 / 2.0))
        )

    def test_hit_testing_rejects_invalid_inputs(self):
        geometry = build_geometry(1000, self.config())
        self.assertEqual(hit_test_guides(None, (0, 0), 5), ())
        self.assertEqual(hit_test_guides(geometry, None, 5), ())
        self.assertEqual(hit_test_guides(geometry, (math.nan, 0), 5), ())
        self.assertEqual(hit_test_guides(geometry, (0, 0), -1), ())
        self.assertEqual(hit_test_guides(geometry, (0, 0), math.inf), ())

    def test_snapshot_is_deterministic(self):
        geometry = build_geometry(
            240,
            self.config(
                width=240,
                height=240,
                columns=24,
                rows=24,
                origin="bottom-left",
            ),
        )
        self.assertEqual(snapshot(geometry), snapshot(geometry))
        self.assertEqual(snapshot(geometry)["canvas"], [0.0, 0.0, 240.0, 240.0])
        self.assertEqual(snapshot(geometry)["gridBounds"], [-10.0, -10.0, 250.0, 250.0])
        self.assertEqual(len(snapshot(geometry)["rings"]), 10)

    def test_non_positive_width_is_a_safe_noop(self):
        self.assertIsNone(build_geometry(0, self.config()))
        self.assertIsNone(build_geometry(-1, self.config()))
        self.assertIsNone(build_geometry(float("nan"), self.config()))


if __name__ == "__main__":
    unittest.main()
