"""Static wiring contracts for the W94 Tags Research client."""
from pathlib import Path
import unittest
from tests.w104_command_test_support import guide_has

from tests.w105_menu_test_support import legacy_menu_projection
ROOT = Path(__file__).resolve().parents[1]


class W94TagsCommandWiringTests(unittest.TestCase):
    def test_production_modules_are_present_and_provenance_tracked(self):
        provenance = (ROOT / "scripts/prove-source-provenance.sh").read_text(encoding="utf-8")
        for module in ("calamus_tags_controller", "calamus_tags_panel", "calamus_tags_runtime"):
            self.assertTrue((ROOT / "calamus" / f"{module}.py").is_file())
            self.assertIn(f'"{module}"', provenance)

    def test_research_menu_and_shortcut_catalog_have_one_tags_command(self):
        ui = legacy_menu_projection()
        self.assertEqual(ui.count('add_item(researchm, "Tags", app.show_tags)'), 1)
        self.assertTrue(guide_has("Research", "Tags", "menu"))

    def test_app_registers_persistent_tags_client_and_thin_show_method(self):
        app = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        composition = (ROOT / "calamus/calamus_research_composition.py").read_text(encoding="utf-8")
        runtime = (ROOT / "calamus/calamus_research_application.py").read_text(encoding="utf-8")
        self.assertIn("from calamus_tags_runtime import TagsRuntime", composition)
        self.assertIn("tags_runtime = TagsRuntime(", composition)
        self.assertIn('"tags", "Tags", tags_runtime.widget', composition)
        self.assertIn('tags_runtime.activate', composition)
        self.assertIn('panel_view.register_client(', composition)
        self.assertIn('lambda client_id=spec.client_id: coordinator.activate(client_id)', composition)
        self.assertIn('def show_tags(self, *_):', runtime)
        self.assertIn('return self.components.panel_runtime.show("tags")', runtime)
        self.assertIn('self._research_components.runtime.show_tags', app)

    def test_help_has_current_menu_entry_and_learning_topic(self):
        guide = (ROOT / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
        self.assertIn("## Current command menu (W95extra mature-source rebuilt candidate)", guide)
        self.assertIn("## Tags", guide)
        self.assertIn("### Tutorial: build a useful tag vocabulary from one article", guide)
        self.assertIn("### First guided exercise", guide)
        self.assertIn("All tags A–Z", guide)
        self.assertIn("Rename / Merge", guide)
        self.assertIn("Scratchpad", guide)


if __name__ == "__main__":
    unittest.main()
