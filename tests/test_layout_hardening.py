import unittest

from calamus_layout import (
    RIGHT_PANEL_DEFAULT_WIDTH,
    RIGHT_PANEL_MAX_FRACTION,
    RIGHT_PANEL_MIN_WIDTH,
)
from calamus_right_panel import calculate_right_panel_width
from calamus_shortcuts import conflicts


class LayoutHardeningTest(unittest.TestCase):
    def test_right_panel_width_is_bounded(self):
        self.assertGreaterEqual(calculate_right_panel_width(400), RIGHT_PANEL_MIN_WIDTH)
        self.assertLessEqual(calculate_right_panel_width(400), RIGHT_PANEL_DEFAULT_WIDTH)
        self.assertEqual(calculate_right_panel_width(2000), RIGHT_PANEL_DEFAULT_WIDTH)
        expected_max = int(900 * RIGHT_PANEL_MAX_FRACTION)
        self.assertLessEqual(
            calculate_right_panel_width(900),
            expected_max if expected_max >= RIGHT_PANEL_MIN_WIDTH else RIGHT_PANEL_DEFAULT_WIDTH,
        )

    def test_shortcut_registry_has_no_conflicts(self):
        self.assertEqual(conflicts(), {})
