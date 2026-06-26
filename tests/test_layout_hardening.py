import unittest

from calamus_layout import CLIP_PANEL_DEFAULT_WIDTH, CLIP_PANEL_MIN_WIDTH, CLIP_PANEL_MAX_FRACTION
from calamus_clip_panel import calculate_clip_panel_width
from calamus_shortcuts import conflicts


class LayoutHardeningTest(unittest.TestCase):
    def test_clip_width_is_bounded(self):
        self.assertGreaterEqual(calculate_clip_panel_width(400), CLIP_PANEL_MIN_WIDTH)
        self.assertLessEqual(calculate_clip_panel_width(400), CLIP_PANEL_DEFAULT_WIDTH)
        self.assertEqual(calculate_clip_panel_width(2000), CLIP_PANEL_DEFAULT_WIDTH)
        self.assertLessEqual(calculate_clip_panel_width(900), int(900 * CLIP_PANEL_MAX_FRACTION) if int(900 * CLIP_PANEL_MAX_FRACTION) >= CLIP_PANEL_MIN_WIDTH else CLIP_PANEL_DEFAULT_WIDTH)

    def test_shortcut_registry_has_no_conflicts(self):
        self.assertEqual(conflicts(), {})
