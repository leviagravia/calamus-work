"""Source-level anti-recurrence contract for the W97 Search/Model rebuild."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class W97SearchModelRebuildContractTests(unittest.TestCase):
    def test_search_uses_explicit_changed_plus_owned_coalescer(self):
        text = (ROOT / "calamus/calamus_reference_panel.py").read_text(encoding="utf-8")
        self.assertIn('self.search.connect("changed", changed)', text)
        self.assertIn("CoalescedQueryDispatcher", text)
        self.assertIn("delay_ms=delay_ms", text)
        self.assertNotIn('self.search.connect("search-changed"', text)

    def test_controller_owns_selected_key(self):
        text = (ROOT / "calamus/calamus_reference_controller.py").read_text(encoding="utf-8")
        self.assertIn("self._selected_key: str | None = None", text)
        self.assertIn("def sync_selection_from_view", text)
        self.assertIn("return self._selected_key", text)

    def test_true_app_waits_for_delivery_not_single_pump(self):
        text = (ROOT / "tests/test_w97_bibliography_app_desktop_e2e.py").read_text(encoding="utf-8")
        self.assertIn("def _until", text)
        self.assertIn('view.last_delivered_query == "patristics"', text)
        self.assertIn('_marker("search-delivered")', text)
        self.assertNotIn('_marker("search-applied")', text)


if __name__ == "__main__":
    unittest.main()
