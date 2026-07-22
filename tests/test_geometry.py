from __future__ import absolute_import

import math
import unittest

from tests import support  # noqa: F401
from icon_grid.config import resolve_config
from icon_grid.geometry import (
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
        return resolve_config(parameters, {}, 700, 1000)[0]

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

    def test_grid_cadence_starts_at_origin(self):
        geometry = build_geometry(
            1000, self.config(width=1000, columns=10, rows=8, majorEvery=2)
        )
        major_x = sorted(
            line.x1 for line in geometry.major_lines if line.x1 == line.x2
        )
        self.assertEqual(major_x, [200.0, 400.0, 600.0, 800.0])
        self.assertTrue(any(line.x1 == 0 for line in geometry.axis_lines))

    def test_every_grid_line_is_axis_aligned_and_spans_the_canvas(self):
        geometry = build_geometry(
            900, self.config(width=900, columns=9, rows=7, height=700, origin="top-right")
        )
        for line in geometry.all_grid_lines():
            if line.x1 == line.x2:
                self.assertEqual((line.y1, line.y2), (geometry.canvas.ymin, geometry.canvas.ymax))
            elif line.y1 == line.y2:
                self.assertEqual((line.x1, line.x2), (geometry.canvas.xmin, geometry.canvas.xmax))
            else:
                self.fail("Grid line is diagonal: {!r}".format(line))

    def test_baseline_offset_moves_canvas_below_zero_and_keeps_baseline_axis(self):
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
        horizontal_axes = [line for line in geometry.axis_lines if line.y1 == line.y2]
        self.assertEqual(horizontal_axes, [Line(0.0, 0.0, 1000.0, 0.0)])
        self.assertTrue(all(circle.cy == 200.0 for circle in geometry.rings))

    def test_centered_odd_grid_has_symmetric_half_cell_gutters(self):
        geometry = build_geometry(
            900, self.config(width=900, columns=9, rows=7, height=700, origin="center")
        )
        verticals = sorted(
            line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
        )
        self.assertEqual(verticals[0], 50.0)
        self.assertEqual(verticals[-1], 850.0)
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, -350.0, 900.0, 350.0))

    def test_live_area_padding_is_in_grid_cells(self):
        geometry = build_geometry(
            1200, self.config(width=1200, columns=24, rows=12, height=600, padding=2)
        )
        self.assertEqual(geometry.live_area.as_tuple(), (100.0, 100.0, 1100.0, 500.0))

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
            1000, self.config(width=1000, height=1000, spokes=8, rings=0)
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
            ),
        )
        probes = {
            "minor": (100.0, 750.0),
            "major": (200.0, 750.0),
            "axis": (0.0, 750.0),
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
            ),
        )
        hits = hit_test_guides(geometry, (200.0, 200.0), 0.001)
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
            ),
        )
        point = (104.0, 750.0)
        self.assertIn(GuideRef("minor", 0), hit_test_guides(geometry, point, 5.0 / 1.0))
        self.assertNotIn(GuideRef("minor", 0), hit_test_guides(geometry, point, 5.0 / 2.0))

    def test_hit_testing_rejects_invalid_inputs(self):
        geometry = build_geometry(1000, self.config())
        self.assertEqual(hit_test_guides(None, (0, 0), 5), ())
        self.assertEqual(hit_test_guides(geometry, None, 5), ())
        self.assertEqual(hit_test_guides(geometry, (math.nan, 0), 5), ())
        self.assertEqual(hit_test_guides(geometry, (0, 0), -1), ())
        self.assertEqual(hit_test_guides(geometry, (0, 0), math.inf), ())

    def test_snapshot_is_deterministic(self):
        geometry = build_geometry(
            240, self.config(width=240, height=240, columns=24, rows=24)
        )
        self.assertEqual(snapshot(geometry), snapshot(geometry))
        self.assertEqual(snapshot(geometry)["canvas"], [0.0, 0.0, 240.0, 240.0])
        self.assertEqual(len(snapshot(geometry)["rings"]), 10)

    def test_non_positive_width_is_a_safe_noop(self):
        self.assertIsNone(build_geometry(0, self.config()))
        self.assertIsNone(build_geometry(-1, self.config()))
        self.assertIsNone(build_geometry(float("nan"), self.config()))


if __name__ == "__main__":
    unittest.main()
