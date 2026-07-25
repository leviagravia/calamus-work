import unittest

from calamus_document_structure import build_document_structure
from calamus_references import ReferenceRecord
from calamus_research_export import (
    ANNOTATED_BIBLIOGRAPHY,
    CITED_BIBLIOGRAPHY,
    FULL_RESEARCH_DOSSIER,
    NOTES_BY_REFERENCE,
    NOTES_DOCUMENT_ORDER,
    build_research_export,
    format_reference_markdown,
    research_export_kinds,
)
from calamus_source_notes import SourceLocator, SourceNote


class ResearchExportPureTests(unittest.TestCase):
    def records(self):
        return (
            ReferenceRecord(
                key="ratzinger1968",
                aliases=("ratzinger-old",),
                authors=("Ratzinger, Joseph",),
                title="Introduction to Christianity",
                year="1968",
                publisher="Herder",
                location="Freiburg",
                annotation="Useful synthesis.",
            ),
            ReferenceRecord(
                key="guardini1950",
                authors=("Guardini, Romano",),
                title="The Lord",
                year="1950",
            ),
            ReferenceRecord(
                key="unused2020",
                title="Unused Work",
                year="2020",
            ),
        )

    def notes(self):
        return (
            SourceNote(
                id="sn-conclusion",
                kind="comment",
                text="A concluding observation.",
                target="#conclusion",
            ),
            SourceNote(
                id="sn-intro",
                kind="quote",
                text="Faith is an encounter.",
                reference_key="ratzinger-old",
                locator=SourceLocator(page="42"),
                target="#intro",
                tags=("faith",),
                comment="Use carefully.",
            ),
            SourceNote(
                id="sn-unresolved",
                kind="paraphrase",
                text="Missing source paraphrase.",
                reference_key="missing-key",
            ),
        )

    def structure(self):
        return build_document_structure(
            "# Paper\n\n## Introduction {#intro}\nText.\n\n"
            "## Conclusion {#conclusion}\nText.\n"
        )

    def artifact(self, kind):
        return build_research_export(
            kind,
            document_name="paper.md",
            document_text="See [@ratzinger-old, p. 4; @guardini1950].",
            records=self.records(),
            notes=self.notes(),
            structure=self.structure(),
        )

    def test_export_kind_surface_is_exact_and_stable(self):
        self.assertEqual(
            research_export_kinds(),
            (
                NOTES_DOCUMENT_ORDER,
                NOTES_BY_REFERENCE,
                CITED_BIBLIOGRAPHY,
                ANNOTATED_BIBLIOGRAPHY,
                FULL_RESEARCH_DOSSIER,
            ),
        )

    def test_document_order_uses_heading_positions_not_sidecar_order(self):
        artifact = self.artifact(NOTES_DOCUMENT_ORDER)
        self.assertLess(artifact.markdown.index("## Introduction"), artifact.markdown.index("## Conclusion"))
        self.assertLess(artifact.markdown.index("sn-intro"), artifact.markdown.index("sn-conclusion"))
        self.assertIn("## Untargeted or Unresolved Notes", artifact.markdown)
        self.assertEqual(artifact.source_note_count, 3)

    def test_notes_by_reference_resolves_aliases_and_reports_missing_keys(self):
        artifact = self.artifact(NOTES_BY_REFERENCE)
        self.assertIn("Ratzinger, Joseph, 1968", artifact.markdown)
        self.assertIn("Unresolved Reference `missing-key`", artifact.markdown)
        self.assertIn("Notes without a Reference", artifact.markdown)
        self.assertEqual(artifact.unresolved_keys, ("missing-key",))

    def test_cited_bibliography_is_first_citation_order_and_excludes_unused(self):
        artifact = self.artifact(CITED_BIBLIOGRAPHY)
        ratzinger = artifact.markdown.index("ratzinger1968")
        guardini = artifact.markdown.index("guardini1950")
        self.assertLess(ratzinger, guardini)
        self.assertNotIn("unused2020", artifact.markdown)
        self.assertNotIn("ratzinger-old`**", artifact.markdown)
        self.assertEqual(artifact.reference_count, 2)

    def test_annotated_bibliography_combines_reference_annotation_and_notes(self):
        artifact = self.artifact(ANNOTATED_BIBLIOGRAPHY)
        self.assertIn("**Reference annotation**", artifact.markdown)
        self.assertIn("Useful synthesis.", artifact.markdown)
        self.assertIn("**Linked Source Notes**", artifact.markdown)
        self.assertIn("Faith is an encounter.", artifact.markdown)
        self.assertNotIn("unused2020", artifact.markdown)
        self.assertEqual(artifact.unresolved_keys, ("missing-key",))

    def test_full_dossier_contains_all_five_derived_sections(self):
        artifact = self.artifact(FULL_RESEARCH_DOSSIER)
        for heading in (
            "# Complete Research Dossier",
            "## Source Notes in Document Order",
            "## Source Notes by Reference",
            "## Bibliography of Cited Sources",
            "## Annotated Bibliography",
        ):
            self.assertIn(heading, artifact.markdown)
        self.assertIn("canonical authorities", artifact.markdown)

    def test_reference_renderer_is_transparent_not_csl_claim(self):
        rendered = format_reference_markdown(self.records()[0])
        self.assertIn("**`ratzinger1968`**", rendered)
        self.assertIn("*Introduction to Christianity*", rendered)
        self.assertIn("Freiburg: Herder, 1968", rendered)

    def test_wrong_types_fail_closed(self):
        with self.assertRaises(ValueError):
            self.artifact("unknown")
        with self.assertRaises(TypeError):
            build_research_export(
                NOTES_DOCUMENT_ORDER,
                document_name="paper.md",
                document_text="",
                records=(object(),),
                notes=(),
                structure=self.structure(),
            )


if __name__ == "__main__":
    unittest.main()
