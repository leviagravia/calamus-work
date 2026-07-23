import os
from pathlib import Path
import tempfile
import unittest

from calamus_citation_controller import CitationController
from calamus_reference_store import MarkdownReferenceStore
from calamus_research_file import FileToken
from calamus_references import ReferenceRecord


class CitationIntegrationTests(unittest.TestCase):
    def test_real_markdown_library_drives_quick_cite_without_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "references.md")
            store = MarkdownReferenceStore(path)
            records = (
                ReferenceRecord(
                    key="ratzinger1968introduction",
                    title="Introduction to Christianity",
                    authors=("Ratzinger, Joseph",),
                    year="1968",
                ),
                ReferenceRecord(
                    key="martini1990lectio",
                    title="Lectio Divina",
                    authors=("Martini, Carlo Maria",),
                    year="1990",
                ),
            )
            result = store.save(records, FileToken(False))
            self.assertTrue(result.saved)
            before = Path(path).read_bytes()
            snapshot = store.load()
            inserted = []
            shown = []
            errors = []
            controller = CitationController(
                reference_records_provider=lambda: snapshot.records,
                insert_text=lambda text: (inserted.append(text), True)[1],
                show_reference=lambda key: (shown.append(key), True)[1],
                choose_key=lambda keys: keys[0] if keys else None,
                on_error=errors.append,
            )

            self.assertTrue(controller.quick_cite("ratzinger1968introduction", "p. 42"))
            self.assertEqual(inserted, ["[@ratzinger1968introduction, p. 42]"])
            text = "The argument follows [@martini1990lectio, chap. 3]."
            self.assertTrue(controller.open_citation(text, text.index("martini") + 2))
            self.assertEqual(shown, ["martini1990lectio"])
            self.assertEqual(errors, [])
            self.assertEqual(Path(path).read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
