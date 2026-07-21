from __future__ import absolute_import

import math
import unittest

from tests import support  # noqa: F401
from icon_grid.config import resolve_config
from icon_grid.geometry import (
    Line,
    build_geometry,
    canvas_for_origin,
    line_width_for_scale,
    snapshot,
)


class GeometryTests(unittest.TestCase):
    def config(self, **values):
        parameters = {"IconGrid." + key: value for key, value in values.items()}
        return resolve_config(parameters, {}, 700, 1000)[0]

    def test_all_origins_have_exact_bounds(self):
        expected = {
            "bottom-left": (0, 0, 1000, 800),
            "bottom-center": (-500, 0, 500, 800),
            "bottom-right": (-1000, 0, 0, 800),
            "center-left": (0, -400, 1000, 400),
            "center": (-500, -400, 500, 400),
            "center-right": (-1000, -400, 0, 400),
            "top-left": (0, -800, 1000, 0),
            "top-center": (-500, -800, 500, 0),
            "top-right": (-1000, -800, 0, 0),
        }
        for origin, bounds in expected.items():
            canvas = canvas_for_origin(1000, 800, origin)
            self.assertEqual(canvas.as_tuple(), bounds, origin)

    def test_grid_cadence_starts_at_origin(self):
        geometry = build_geometry(1000, self.config(columns=10, rows=8, majorEvery=2))
        major_x = sorted(
            line.x1 for line in geometry.major_lines if line.x1 == line.x2
        )
        self.assertEqual(major_x, [200.0, 400.0, 600.0, 800.0])
        self.assertTrue(any(line.x1 == 0 for line in geometry.axis_lines))

    def test_every_grid_line_is_axis_aligned_and_spans_the_canvas(self):
        geometry = build_geometry(
            900, self.config(columns=9, rows=7, height=700, origin="top-right")
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
            self.config(height=800, rows=8, origin="bottom-left", baselineOffset=200),
        )
        self.assertEqual(geometry.canvas.as_tuple(), (0.0, -200.0, 1000.0, 600.0))
        self.assertEqual(geometry.center, (500.0, 200.0))
        horizontal_axes = [line for line in geometry.axis_lines if line.y1 == line.y2]
        self.assertEqual(horizontal_axes, [Line(0.0, 0.0, 1000.0, 0.0)])
        self.assertTrue(all(circle.cy == 200.0 for circle in geometry.rings))

    def test_centered_odd_grid_has_symmetric_half_cell_gutters(self):
        geometry = build_geometry(
            900, self.config(columns=9, rows=7, height=700, origin="center")
        )
        verticals = sorted(
            line.x1 for line in geometry.all_grid_lines() if line.x1 == line.x2
        )
        self.assertEqual(verticals[0], -400.0)
        self.assertEqual(verticals[-1], 400.0)
        self.assertEqual(geometry.canvas.as_tuple(), (-450.0, -350.0, 450.0, 350.0))

    def test_live_area_padding_is_in_grid_cells(self):
        geometry = build_geometry(
            1200, self.config(columns=24, rows=12, height=600, padding=2)
        )
        self.assertEqual(geometry.live_area.as_tuple(), (100.0, 100.0, 1100.0, 500.0))

    def test_rings_are_true_circles_centered_in_rectangular_canvas(self):
        geometry = build_geometry(
            1200, self.config(height=800, rings=4, origin="top-right")
        )
        self.assertEqual(geometry.center, (-600.0, -400.0))
        expected_step = (800.0 - 2 * (2 * 800.0 / 24.0)) / 2.0 / 4.0
        for circle, expected_radius in zip(geometry.rings, [expected_step * i for i in range(1, 5)]):
            self.assertAlmostEqual(circle.radius, expected_radius)
        for circle in geometry.rings:
            self.assertEqual(circle.cx, -600.0)
            self.assertEqual(circle.cy, -400.0)

    def test_spokes_are_evenly_spaced_on_outer_live_circle(self):
        geometry = build_geometry(1000, self.config(height=1000, spokes=8, rings=0))
        self.assertEqual(len(geometry.spokes), 8)
        endpoints = {(round(line.x2, 6), round(line.y2, 6)) for line in geometry.spokes}
        self.assertIn((916.666667, 500.0), endpoints)
        self.assertIn((500.0, 83.333333), endpoints)
        for line in geometry.spokes:
            radius = math.hypot(line.x2 - geometry.center[0], line.y2 - geometry.center[1])
            self.assertAlmostEqual(radius, geometry.live_radius)

    def test_material_keyline_proportions(self):
        geometry = build_geometry(1000, self.config(height=1000, showKeylines=True))
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

    def test_snapshot_is_deterministic(self):
        geometry = build_geometry(240, self.config(height=240, columns=24, rows=24))
        self.assertEqual(snapshot(geometry), snapshot(geometry))
        self.assertEqual(snapshot(geometry)["canvas"], [0.0, 0.0, 240.0, 240.0])
        self.assertEqual(len(snapshot(geometry)["rings"]), 10)

    def test_non_positive_width_is_a_safe_noop(self):
        self.assertIsNone(build_geometry(0, self.config()))
        self.assertIsNone(build_geometry(-1, self.config()))
        self.assertIsNone(build_geometry(float("nan"), self.config()))


if __name__ == "__main__":
    unittest.main()
