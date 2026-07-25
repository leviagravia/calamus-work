import os
import tempfile
import unittest
from pathlib import Path

from calamus_document_structure import build_document_structure
from calamus_reference_store import MarkdownReferenceStore
from calamus_references import ReferenceRecord
from calamus_research_export import CITED_BIBLIOGRAPHY
from calamus_research_export_controller import ResearchExportController
from calamus_research_export_runtime import ResearchExportRuntime


class ResearchExportRuntimeTests(unittest.TestCase):
    def fixture(self, tmp, chooser):
        document = os.path.join(tmp, "paper.md")
        Path(document).write_text("See [@ref1].", encoding="utf-8")
        store = MarkdownReferenceStore(os.path.join(tmp, "references.md"))
        store.save(
            (ReferenceRecord(key="ref1", title="Title"),),
            store.load().token,
        )
        controller = ResearchExportController(
            reference_store=store,
            document_path_provider=lambda: document,
            document_text_provider=lambda: "See [@ref1].",
            document_structure_provider=lambda: build_document_structure("See [@ref1]."),
        )
        events = []
        runtime = ResearchExportRuntime(
            object(),
            controller,
            document_path_provider=lambda: document,
            show_error=lambda message: events.append(("error", message)),
            show_info=lambda message: events.append(("info", message)),
            chooser=chooser,
        )
        return runtime, events

    def test_cancel_performs_no_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            runtime, events = self.fixture(tmp, lambda *_: None)
            self.assertFalse(runtime.export())
            self.assertEqual(events, [])

    def test_success_reports_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = os.path.join(tmp, "cited.md")
            runtime, events = self.fixture(tmp, lambda *_: (CITED_BIBLIOGRAPHY, output))
            self.assertTrue(runtime.export())
            self.assertTrue(Path(output).exists())
            self.assertEqual(events[0][0], "info")
            self.assertIn(output, events[0][1])


if __name__ == "__main__":
    unittest.main()
