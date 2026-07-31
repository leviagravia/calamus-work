from __future__ import annotations

import unittest

from calamus_typewriter import TypewriterSettings, compute_typewriter_target, runway_margin
from calamus_viewport import ViewportGeometry, compute_vertical_reveal


class W95ExtraViewportPolicyTests(unittest.TestCase):
    def geometry(self, **overrides):
        values = dict(
            caret_y=500.0,
            caret_height=20.0,
            visible_y=200.0,
            visible_height=600.0,
            lower=0.0,
            upper=3000.0,
            page_size=600.0,
            top_margin=0.0,
        )
        values.update(overrides)
        return ViewportGeometry(**values)

    def test_ordinary_reveal_is_noop_inside_safe_band(self):
        target = compute_vertical_reveal(
            caret_y=500, caret_height=20, visible_y=200, visible_height=600,
            lower=0, upper=3000, page_size=600, within_margin=0.15,
        )
        self.assertIsNone(target)

    def test_ordinary_reveal_centers_only_when_outside(self):
        target = compute_vertical_reveal(
            caret_y=1200, caret_height=20, visible_y=200, visible_height=600,
            lower=0, upper=3000, page_size=600, within_margin=0.15,
            center_if_outside=True,
        )
        self.assertEqual(target, 910.0)

    def test_typewriter_keeps_natural_start_until_midpoint_is_attainable(self):
        decision = compute_typewriter_target(
            self.geometry(caret_y=20, visible_y=0), TypewriterSettings(), reached=False
        )
        self.assertTrue(decision.geometry_ready)
        self.assertFalse(decision.reached)
        self.assertIsNone(decision.target)

    def test_typewriter_latches_at_first_attainable_midpoint(self):
        decision = compute_typewriter_target(
            self.geometry(caret_y=800, visible_y=0), TypewriterSettings(), reached=False
        )
        self.assertTrue(decision.reached)
        self.assertEqual(decision.target, 510.0)

    def test_typewriter_maintains_midpoint_after_latch_and_clamps(self):
        decision = compute_typewriter_target(
            self.geometry(caret_y=2950, visible_y=2200, upper=3600),
            TypewriterSettings(),
            reached=True,
        )
        self.assertTrue(decision.reached)
        self.assertEqual(decision.target, 2660.0)

    def test_typewriter_noops_inside_tolerance(self):
        decision = compute_typewriter_target(
            self.geometry(caret_y=490, caret_height=20, visible_y=200),
            TypewriterSettings(tolerance_px=2),
            reached=True,
        )
        self.assertTrue(decision.reached)
        self.assertIsNone(decision.target)

    def test_runway_is_view_only_fraction_plus_existing_margin(self):
        self.assertEqual(runway_margin(600, TypewriterSettings(), base_margin=12), 342)

    def test_invalid_policy_fails_closed(self):
        with self.assertRaises(ValueError):
            TypewriterSettings(target_fraction=0.1)
        with self.assertRaises(ValueError):
            TypewriterSettings(runway_fraction=1.1)
        with self.assertRaises(ValueError):
            compute_vertical_reveal(
                caret_y=0, caret_height=1, visible_y=0, visible_height=10,
                lower=0, upper=10, page_size=10, within_margin=0.7,
            )


if __name__ == "__main__":
    unittest.main()
