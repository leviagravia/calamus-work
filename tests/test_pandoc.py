"""Pure W90 model proofs for the closed Pandoc/citeproc surface."""
from pathlib import Path
import tempfile
import unittest

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
    canonicalize_document_citations,
    pandoc_formats,
    select_references,
    suggested_output_name,
)
from calamus_reference_sets import ReferenceSet
from calamus_pandoc_artifact_assertions import (
    contains_semantic_text,
    normalize_rendered_text,
)
from calamus_references import ReferenceRecord


def records():
    return (
        ReferenceRecord("ratzinger1968", "Introduction to Christianity", authors=("Ratzinger, Joseph",), year="1968", aliases=("ratzinger-old",)),
        ReferenceRecord("guardini1950", "The Lord", authors=("Guardini, Romano",), year="1950"),
        ReferenceRecord("deLubac1944", "Catholicism", authors=("de Lubac, Henri",), year="1944"),
    )


class PandocModelTests(unittest.TestCase):
    def test_format_registry_is_small_product_specific_and_pdf_free(self):
        bibliography = tuple(item.id for item in pandoc_formats(PRODUCT_BIBLIOGRAPHY))
        document = tuple(item.id for item in pandoc_formats(PRODUCT_DOCUMENT))
        self.assertEqual(
            bibliography,
            (FORMAT_PLAIN, FORMAT_HTML, FORMAT_ODT, FORMAT_DOCX, FORMAT_RTF, FORMAT_LATEX),
        )
        self.assertEqual(
            document,
            (FORMAT_HTML, FORMAT_ODT, FORMAT_DOCX, FORMAT_EPUB, FORMAT_RTF, FORMAT_LATEX),
        )
        self.assertNotIn("pdf", bibliography + document)

    def test_request_requires_exact_product_extension_and_reference_set(self):
        with tempfile.TemporaryDirectory() as directory:
            valid = PandocExportRequest(
                PRODUCT_DOCUMENT,
                SCOPE_CITED,
                FORMAT_ODT,
                str(Path(directory) / "paper.odt"),
            )
            self.assertEqual(valid.destination, str(Path(directory) / "paper.odt"))
            with self.assertRaisesRegex(ValueError, "requires the .odt"):
                PandocExportRequest(
                    PRODUCT_DOCUMENT,
                    SCOPE_CITED,
                    FORMAT_ODT,
                    str(Path(directory) / "paper.docx"),
                )
            with self.assertRaisesRegex(ValueError, "Choose one Reference Set"):
                PandocExportRequest(
                    PRODUCT_BIBLIOGRAPHY,
                    SCOPE_REFERENCE_SET,
                    FORMAT_PLAIN,
                    str(Path(directory) / "refs.txt"),
                )

    def test_alias_citations_are_canonicalized_only_in_derived_projection(self):
        original = "Claim [@ratzinger-old, p. 2]. `@ratzinger-old`\n"
        projected, cited = canonicalize_document_citations(records(), original)
        self.assertEqual(cited, ("ratzinger1968",))
        self.assertEqual(projected, "Claim [@ratzinger1968, p. 2]. `@ratzinger-old`\n")
        self.assertIn("@ratzinger-old", original)

    def test_cited_scope_preserves_first_citation_order(self):
        selection = select_references(
            records(),
            (),
            "A [@guardini1950]. B [@ratzinger-old]. A [@guardini1950].",
            product=PRODUCT_BIBLIOGRAPHY,
            scope=SCOPE_CITED,
        )
        self.assertEqual(selection.keys, ("guardini1950", "ratzinger1968"))

    def test_all_scope_preserves_library_order(self):
        selection = select_references(
            records(), (), "", product=PRODUCT_BIBLIOGRAPHY, scope=SCOPE_ALL
        )
        self.assertEqual(selection.keys, tuple(item.key for item in records()))

    def test_reference_set_scope_is_case_sensitive_canonical_and_ordered(self):
        sets = (ReferenceSet("Core sources", members=("guardini1950", "ratzinger-old")),)
        selection = select_references(
            records(),
            sets,
            "",
            product=PRODUCT_BIBLIOGRAPHY,
            scope=SCOPE_REFERENCE_SET,
            reference_set_name="Core sources",
        )
        self.assertEqual(selection.keys, ("guardini1950", "ratzinger1968"))
        self.assertEqual(selection.reference_set_name, "Core sources")
        with self.assertRaisesRegex(ValueError, "case-sensitive"):
            select_references(
                records(),
                sets,
                "",
                product=PRODUCT_BIBLIOGRAPHY,
                scope=SCOPE_REFERENCE_SET,
                reference_set_name="Core Sources",
            )

    def test_document_scope_must_include_every_cited_reference(self):
        sets = (ReferenceSet("One", members=("guardini1950",)),)
        with self.assertRaisesRegex(ValueError, "omits citation"):
            select_references(
                records(),
                sets,
                "Cited [@ratzinger1968].",
                product=PRODUCT_DOCUMENT,
                scope=SCOPE_REFERENCE_SET,
                reference_set_name="One",
            )

    def test_missing_and_ambiguous_citations_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "missing Reference"):
            select_references(
                records(), (), "[@missing]", product=PRODUCT_BIBLIOGRAPHY, scope=SCOPE_CITED
            )
        ambiguous = records() + (
            ReferenceRecord("other", "Other", aliases=("ratzinger-old",)),
        )
        with self.assertRaisesRegex(ValueError, "identity"):
            select_references(
                ambiguous, (), "[@ratzinger-old]", product=PRODUCT_BIBLIOGRAPHY, scope=SCOPE_CITED
            )

    def test_remote_media_is_blocked_but_links_and_code_examples_are_allowed(self):
        with self.assertRaisesRegex(ValueError, "Remote images or media"):
            select_references(
                records(),
                (),
                "A [link](https://example.org) and ![remote](https://example.org/a.png) [@ratzinger1968].",
                product=PRODUCT_DOCUMENT,
                scope=SCOPE_CITED,
            )
        allowed = select_references(
            records(),
            (),
            "A [link](https://example.org) and `![example](https://example.org/a.png)` [@ratzinger1968].",
            product=PRODUCT_DOCUMENT,
            scope=SCOPE_CITED,
        )
        self.assertEqual(allowed.keys, ("ratzinger1968",))
        with self.assertRaisesRegex(ValueError, "Remote images or media"):
            select_references(
                records(),
                (),
                '<img src="https://example.org/a.png"> [@ratzinger1968]',
                product=PRODUCT_DOCUMENT,
                scope=SCOPE_CITED,
            )


    def test_rendered_artifact_normalization_collapses_only_whitespace(self):
        wrapped = "Herder and\nHerder.\r\n"
        self.assertEqual(normalize_rendered_text(wrapped), "Herder and Herder.")
        self.assertTrue(contains_semantic_text(wrapped, "Herder and Herder"))

    def test_rendered_artifact_normalization_preserves_list_separator_semantics(self):
        self.assertFalse(contains_semantic_text("Herder; Herder", "Herder and Herder"))
        self.assertTrue(contains_semantic_text("Herder; Herder", "Herder; Herder"))

    def test_rendered_artifact_normalization_can_casefold_titles(self):
        rendered = "Introduction to christianity.\nThe lord."
        self.assertTrue(contains_semantic_text(rendered, "Introduction to Christianity", casefold=True))
        self.assertTrue(contains_semantic_text(rendered, "The Lord", casefold=True))

    def test_suggested_names_are_bounded_and_product_specific(self):
        self.assertEqual(
            suggested_output_name("/tmp/My Paper.md", PRODUCT_DOCUMENT, FORMAT_DOCX),
            "My Paper-with-citations.docx",
        )
        self.assertEqual(
            suggested_output_name(None, PRODUCT_BIBLIOGRAPHY, FORMAT_PLAIN),
            "calamus-bibliography.txt",
        )


if __name__ == "__main__":
    unittest.main()
