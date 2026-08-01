"""Real-filesystem and real-Pandoc proofs for the W90 controller."""
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

from calamus_pandoc import (
    FORMAT_DOCX,
    FORMAT_EPUB,
    FORMAT_HTML,
    FORMAT_LATEX,
    FORMAT_ODT,
    FORMAT_PLAIN,
    FORMAT_RTF,
    PRODUCT_BIBLIOGRAPHY,
    PRODUCT_DOCUMENT,
    SCOPE_ALL,
    SCOPE_CITED,
    SCOPE_REFERENCE_SET,
    PandocExportRequest,
)
from calamus_pandoc_controller import PandocExportController
from tests.calamus_pandoc_artifact_assertions import contains_semantic_text
from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_sets import ReferenceSet, serialize_reference_sets_markdown
from calamus_reference_store import MarkdownReferenceStore, serialize_references_markdown
from calamus_references import ReferenceRecord
from calamus_research_file import atomic_write_utf8


_CSL = '''<?xml version="1.0" encoding="utf-8"?>
<style xmlns="http://purl.org/net/xbiblio/csl" version="1.0" class="in-text">
  <info><title>Calamus Test</title><id>https://example.invalid/calamus-test</id><updated>2026-07-26T00:00:00+00:00</updated></info>
  <citation><layout prefix="(" suffix=")"><text variable="title"/></layout></citation>
  <bibliography><layout suffix="."><text variable="title"/></layout></bibliography>
</style>
'''


@unittest.skipUnless(shutil.which("pandoc"), "real Pandoc unavailable")
class PandocControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.data.mkdir()
        self.references_path = self.data / "references.md"
        self.sets_path = self.data / "reference-sets.md"
        self.document_path = self.root / "paper.md"
        self.document_text = "# Thesis\n\nA claim [@ratzinger-old, p. 3].\n"
        self.document_path.write_text(self.document_text, encoding="utf-8")
        self.records = (
            ReferenceRecord(
                "ratzinger1968",
                "Introduction to Christianity",
                authors=("Ratzinger, Joseph",),
                year="1968",
                publisher="Herder and Herder",
                aliases=("ratzinger-old",),
            ),
            ReferenceRecord(
                "guardini1950",
                "The Lord",
                authors=("Guardini, Romano",),
                year="1950",
                publisher="Regnery",
            ),
        )
        atomic_write_utf8(str(self.references_path), serialize_references_markdown(self.records))
        atomic_write_utf8(
            str(self.sets_path),
            serialize_reference_sets_markdown(
                (ReferenceSet("Core sources", members=("guardini1950", "ratzinger-old")),)
            ),
        )
        self.reference_store = MarkdownReferenceStore(str(self.references_path))
        self.set_store = MarkdownReferenceSetStore(str(self.sets_path))
        self.controller = PandocExportController(
            self.reference_store,
            self.set_store,
            document_path_provider=lambda: str(self.document_path),
            document_text_provider=lambda: self.document_text,
        )

    def tearDown(self):
        self.controller.cancel_active()
        self.temp.cleanup()

    def request(self, product, scope, format_id, name, set_name="", csl=""):
        return PandocExportRequest(
            product,
            scope,
            format_id,
            str(self.root / name),
            set_name,
            csl,
        )

    def test_real_pandoc_plain_bibliography_preview_and_atomic_export(self):
        request = self.request(
            PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, "bibliography.txt"
        )
        plan = self.controller.prepare_export(request)
        preview = self.controller.build_preview(plan)
        self.assertTrue(preview.succeeded, preview.message)
        self.assertIn("Introduction to Christianity", preview.text)
        self.assertIn("The Lord", preview.text)
        result = self.controller.apply_export(plan)
        self.assertTrue(result.succeeded, result.message)
        output = Path(result.path).read_text(encoding="utf-8")
        self.assertTrue(
            contains_semantic_text(output, "Introduction to Christianity", casefold=True)
        )
        self.assertTrue(contains_semantic_text(output, "The Lord", casefold=True))
        self.assertTrue(contains_semantic_text(output, "Herder and Herder"))
        self.assertFalse(contains_semantic_text(output, "Herder; Herder"))
        self.assertFalse(any(self.root.glob(".calamus-pandoc-*.stage")))

    def test_real_document_docx_canonicalizes_alias_without_mutating_source(self):
        original = self.document_path.read_bytes()
        request = self.request(
            PRODUCT_DOCUMENT, SCOPE_CITED, FORMAT_DOCX, "paper.docx"
        )
        plan = self.controller.prepare_export(request)
        self.assertIn("@ratzinger1968", plan.selection.document_text)
        self.assertNotIn("@ratzinger-old", plan.selection.document_text)
        preview = self.controller.build_preview(plan)
        self.assertTrue(preview.succeeded, preview.message)
        self.assertIn("Introduction to Christianity", preview.text)
        result = self.controller.apply_export(plan)
        self.assertTrue(result.succeeded, result.message)
        with zipfile.ZipFile(result.path) as archive:
            self.assertIn("word/document.xml", archive.namelist())
        self.assertEqual(self.document_path.read_bytes(), original)
        self.assertEqual(self.references_path.read_text(encoding="utf-8"), serialize_references_markdown(self.records))

    def test_real_document_odt_preserves_scalar_biblatex_publisher_with_and(self):
        request = self.request(
            PRODUCT_DOCUMENT, SCOPE_CITED, FORMAT_ODT, "paper-publisher.odt"
        )
        plan = self.controller.prepare_export(request)
        result = self.controller.apply_export(plan)
        self.assertTrue(result.succeeded, result.message)
        with zipfile.ZipFile(result.path) as archive:
            xml = archive.read("content.xml")
        import xml.etree.ElementTree as ET
        rendered = "".join(ET.fromstring(xml).itertext())
        self.assertTrue(contains_semantic_text(rendered, "Herder and Herder"))
        self.assertFalse(contains_semantic_text(rendered, "Herder; Herder"))

    def test_reference_set_scope_and_custom_csl_are_exact(self):
        csl = self.root / "test.csl"
        csl.write_text(_CSL, encoding="utf-8")
        request = self.request(
            PRODUCT_BIBLIOGRAPHY,
            SCOPE_REFERENCE_SET,
            FORMAT_HTML,
            "core.html",
            "Core sources",
            str(csl),
        )
        plan = self.controller.prepare_export(request)
        self.assertEqual(plan.selection.keys, ("guardini1950", "ratzinger1968"))
        preview = self.controller.build_preview(plan)
        self.assertTrue(preview.succeeded, preview.message)
        preview_folded = preview.text.casefold()
        self.assertIn("the lord", preview_folded)
        self.assertIn("introduction to christianity", preview_folded)
        result = self.controller.apply_export(plan)
        self.assertTrue(result.succeeded, result.message)
        html_folded = Path(result.path).read_text(encoding="utf-8").casefold()
        self.assertIn("the lord", html_folded)
        self.assertIn("introduction to christianity", html_folded)

    def test_real_pandoc_closed_format_matrix_produces_nonempty_artifacts(self):
        bibliography_formats = (
            (FORMAT_PLAIN, "refs.txt"),
            (FORMAT_HTML, "refs.html"),
            (FORMAT_ODT, "refs.odt"),
            (FORMAT_DOCX, "refs.docx"),
            (FORMAT_RTF, "refs.rtf"),
            (FORMAT_LATEX, "refs.tex"),
        )
        for format_id, filename in bibliography_formats:
            with self.subTest(product="bibliography", format=format_id):
                plan = self.controller.prepare_export(
                    self.request(PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, format_id, filename)
                )
                result = self.controller.apply_export(plan)
                self.assertTrue(result.succeeded, result.message)
                self.assertGreater(Path(result.path).stat().st_size, 0)
        document_formats = (
            (FORMAT_HTML, "paper.html"),
            (FORMAT_ODT, "paper.odt"),
            (FORMAT_DOCX, "paper-matrix.docx"),
            (FORMAT_EPUB, "paper.epub"),
            (FORMAT_RTF, "paper.rtf"),
            (FORMAT_LATEX, "paper.tex"),
        )
        for format_id, filename in document_formats:
            with self.subTest(product="document", format=format_id):
                plan = self.controller.prepare_export(
                    self.request(PRODUCT_DOCUMENT, SCOPE_CITED, format_id, filename)
                )
                result = self.controller.apply_export(plan)
                self.assertTrue(result.succeeded, result.message)
                self.assertGreater(Path(result.path).stat().st_size, 0)

    def test_reference_set_and_csl_changes_after_preview_are_stale(self):
        plan = self.controller.prepare_export(
            self.request(
                PRODUCT_BIBLIOGRAPHY,
                SCOPE_REFERENCE_SET,
                FORMAT_PLAIN,
                "set-stale.txt",
                "Core sources",
            )
        )
        atomic_write_utf8(
            str(self.sets_path),
            serialize_reference_sets_markdown((ReferenceSet("Core sources", members=("guardini1950",)),)),
        )
        self.assertEqual(self.controller.apply_export(plan).status, "stale")
        atomic_write_utf8(
            str(self.sets_path),
            serialize_reference_sets_markdown((ReferenceSet("Core sources", members=("guardini1950", "ratzinger-old")),)),
        )
        csl = self.root / "stale.csl"
        csl.write_text(_CSL, encoding="utf-8")
        plan = self.controller.prepare_export(
            self.request(PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, "csl-stale.txt", csl=str(csl))
        )
        csl.write_text(_CSL.replace("Calamus Test", "Changed Style"), encoding="utf-8")
        self.assertEqual(self.controller.apply_export(plan).status, "stale")

    def test_stale_references_after_preview_write_nothing(self):
        destination = self.root / "stale.txt"
        plan = self.controller.prepare_export(
            self.request(PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, destination.name)
        )
        self.assertTrue(self.controller.build_preview(plan).succeeded)
        changed = self.records + (ReferenceRecord("new2026", "New source"),)
        atomic_write_utf8(str(self.references_path), serialize_references_markdown(changed))
        result = self.controller.apply_export(plan)
        self.assertEqual(result.status, "stale")
        self.assertFalse(destination.exists())

    def test_destination_creation_after_preview_is_stale_and_preserved(self):
        destination = self.root / "external.txt"
        plan = self.controller.prepare_export(
            self.request(PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, destination.name)
        )
        destination.write_text("external", encoding="utf-8")
        result = self.controller.apply_export(plan)
        self.assertEqual(result.status, "stale")
        self.assertEqual(destination.read_text(encoding="utf-8"), "external")

    def test_document_buffer_or_disk_change_is_stale(self):
        plan = self.controller.prepare_export(
            self.request(PRODUCT_DOCUMENT, SCOPE_CITED, FORMAT_DOCX, "stale.docx")
        )
        self.document_text += "Changed in buffer.\n"
        self.assertEqual(self.controller.apply_export(plan).status, "stale")
        self.document_text = "# Thesis\n\nA claim [@ratzinger-old, p. 3].\n"
        plan = self.controller.prepare_export(
            self.request(PRODUCT_DOCUMENT, SCOPE_CITED, FORMAT_DOCX, "stale2.docx")
        )
        self.document_path.write_text(self.document_text + "disk", encoding="utf-8")
        self.assertEqual(self.controller.apply_export(plan).status, "stale")

    def test_destination_directory_replacement_is_stale(self):
        output_dir = self.root / "exports"
        output_dir.mkdir()
        request = PandocExportRequest(
            PRODUCT_BIBLIOGRAPHY,
            SCOPE_ALL,
            FORMAT_PLAIN,
            str(output_dir / "bibliography.txt"),
        )
        plan = self.controller.prepare_export(request)
        output_dir.rename(self.root / "exports-old")
        output_dir.mkdir()
        result = self.controller.apply_export(plan)
        self.assertEqual(result.status, "stale")
        self.assertFalse((output_dir / "bibliography.txt").exists())

    def test_authorities_csl_and_symlink_destinations_are_protected(self):
        # Exact authority protection with matching extension.
        text_authority = self.root / "current.txt"
        text_authority.write_text("[@ratzinger1968]", encoding="utf-8")
        controller = PandocExportController(
            self.reference_store,
            self.set_store,
            document_path_provider=lambda: str(text_authority),
            document_text_provider=lambda: text_authority.read_text(encoding="utf-8"),
        )
        with self.assertRaisesRegex(ValueError, "cannot replace"):
            controller.prepare_export(
                PandocExportRequest(
                    PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, str(text_authority)
                )
            )
        csl = self.root / "style.csl"
        csl.write_text(_CSL, encoding="utf-8")
        csl_link = self.root / "style-link.csl"
        csl_link.symlink_to(csl)
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            self.controller.prepare_export(
                self.request(
                    PRODUCT_BIBLIOGRAPHY,
                    SCOPE_ALL,
                    FORMAT_PLAIN,
                    "out.txt",
                    csl=str(csl_link),
                )
            )
        destination = self.root / "link.txt"
        destination.symlink_to(self.root / "target.txt")
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            self.controller.prepare_export(
                self.request(PRODUCT_BIBLIOGRAPHY, SCOPE_ALL, FORMAT_PLAIN, "link.txt")
            )


if __name__ == "__main__":
    unittest.main()
