"""W92 Research efficiency and managed-sidecar regression tests."""
from pathlib import Path
import tempfile
import unittest

from calamus_managed_sidecars import (
    MANAGED_DOCUMENT_SIDECAR_SUFFIXES,
    SCRATCHPAD_SIDECAR,
    SOURCE_NOTES_SIDECAR,
    document_sidecar_path,
    is_managed_sidecar_name,
    sidecar_spec_for_suffix,
)
from calamus_research_panel_view import ResearchPanelViewAdapter


ROOT = Path(__file__).resolve().parents[1]


class FakeSelector:
    def __init__(self, active="scratchpad"):
        self.active = active
    def get_active_id(self):
        return self.active
    def set_active_id(self, value):
        self.active = value


class FakeStack:
    def __init__(self):
        self.visible = "clip-collection"
        self.calls = []
    def set_visible_child_name(self, value):
        self.visible = value
        self.calls.append(value)
    def get_visible_child_name(self):
        return self.visible


class W92ResearchEfficiencyTests(unittest.TestCase):
    def test_selector_change_activates_exactly_once(self):
        adapter = ResearchPanelViewAdapter.__new__(ResearchPanelViewAdapter)
        adapter._clients = {"scratchpad": (object(), lambda: activated.append("scratchpad"))}
        adapter._syncing_selector = False
        adapter.selector = FakeSelector("scratchpad")
        adapter.stack = FakeStack()
        activated = []
        adapter._on_selector_changed(adapter.selector)
        self.assertEqual(adapter.stack.calls, ["scratchpad"])
        self.assertEqual(activated, ["scratchpad"])

    def test_managed_sidecar_registry_is_single_and_case_safe(self):
        self.assertEqual(
            MANAGED_DOCUMENT_SIDECAR_SUFFIXES,
            (".source-notes.md", ".scratchpad.md"),
        )
        self.assertEqual(sidecar_spec_for_suffix(".SCRATCHPAD.MD"), SCRATCHPAD_SIDECAR)
        self.assertEqual(sidecar_spec_for_suffix(".source-notes.md"), SOURCE_NOTES_SIDECAR)
        self.assertTrue(is_managed_sidecar_name("Chapter.MD.SCRATCHPAD.MD"))
        self.assertFalse(is_managed_sidecar_name("scratchpad.md"))

    def test_document_sidecar_paths_expand_and_remain_document_owned(self):
        with tempfile.TemporaryDirectory() as tmp:
            document = str(Path(tmp) / "Chapter.md")
            self.assertEqual(
                document_sidecar_path(document, SCRATCHPAD_SIDECAR),
                document + ".scratchpad.md",
            )
            self.assertEqual(
                document_sidecar_path(document, SOURCE_NOTES_SIDECAR),
                document + ".source-notes.md",
            )
            self.assertIsNone(document_sidecar_path("", SCRATCHPAD_SIDECAR))

    def test_user_guide_integrates_scratchpad_into_research_authorities(self):
        guide = (ROOT / "share/doc/calamus/USER_GUIDE.md").read_text(encoding="utf-8")
        for required in (
            "The six objects you must distinguish",
            "Le autorità sono cinque",
            "Documento.md.scratchpad.md",
            "Scratchpad Basic: dal pensiero provvisorio al testo",
            "Ctrl+Alt+S",
            "Ctrl+Alt+Shift+S",
            "Il pulsante **Refresh**",
            "tutti i sidecar `.scratchpad.md`",
            "Scratchpad Entry",
            "Research → Scratchpad` or `Ctrl+Alt+S",
        ):
            self.assertIn(required, guide)
        self.assertNotIn("risultati ricostruiti leggendo i quattro file", guide)


    def test_scratchpad_list_key_dispatch_is_small_and_deterministic(self):
        from calamus_scratchpad_panel import _dispatch_scratchpad_list_key
        calls = []
        add = lambda: calls.append("new")
        delete = lambda: calls.append("delete")
        refresh = lambda: calls.append("refresh")
        for key, expected in (("Insert", "new"), ("Delete", "delete"), ("KP_Delete", "delete"), ("F5", "refresh")):
            self.assertTrue(_dispatch_scratchpad_list_key(key, add, delete, refresh))
            self.assertEqual(calls[-1], expected)
        self.assertFalse(_dispatch_scratchpad_list_key("Return", add, delete, refresh))

    def test_refresh_forces_document_reload(self):
        from calamus_scratchpad_runtime import ScratchpadRuntime
        runtime = ScratchpadRuntime.__new__(ScratchpadRuntime)
        calls = []
        runtime.sync_document = lambda *, force=False: calls.append(force) or True
        self.assertTrue(runtime.on_refresh())
        self.assertEqual(calls, [True])

    def test_research_shortcuts_are_unique(self):
        from calamus_shortcuts import SHORTCUTS, conflicts
        self.assertEqual(conflicts(SHORTCUTS), {})
        by_command = {item.command: item.shortcut for item in SHORTCUTS}
        self.assertEqual(by_command["Scratchpad"], "Ctrl+Alt+S")
        self.assertEqual(
            by_command["Capture Selection in Scratchpad"],
            "Ctrl+Alt+Shift+S",
        )


if __name__ == "__main__":
    unittest.main()
