import os
import tempfile
import unittest
from pathlib import Path

from calamus_bibliography import (
    BibliographyContext,
    BibliographyFilters,
    build_bibliography_context,
    build_delete_impact,
    complete_search_text,
    duplicate_reference,
    format_reference_detail,
    project_references,
    render_markdown_bibliography,
    render_plain_bibliography,
)
from calamus_reference_sets import ReferenceSet
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceNote


class W97BibliographyModelTests(unittest.TestCase):
    def records(self, file_path=""):
        return (
            ReferenceRecord(
                key="alpha2020", title="Alpha Book", type="book",
                authors=("Rossi, Anna",), year="2020", tags=("theology",),
                volume="2", pages="10-20", language="it", file_path=file_path,
                extra_fields=(("Custom Field", "Patristics"),),
            ),
            ReferenceRecord(
                key="beta2021", title="Beta Article", type="journal-article",
                authors=("Bianchi, Bruno",), year="2021", tags=("history",),
                doi="10.1000/beta",
            ),
            ReferenceRecord(
                key="gamma2019", title="Gamma Thesis", type="thesis",
                year="2019",
            ),
        )

    def test_complete_search_includes_every_core_and_extra_field(self):
        record = self.records()[0]
        haystack = complete_search_text(record)
        for needle in ("alpha2020", "alpha book", "volume", "2", "10-20", "it", "custom field", "patristics"):
            self.assertIn(needle, haystack)

    def test_projection_combines_query_filters_context_and_stable_sort(self):
        records = self.records()
        context = BibliographyContext(
            cited_keys=frozenset({"beta2021"}),
            source_note_keys=frozenset({"alpha2020"}),
            issue_severities_by_key=(("gamma2019", ("warning", "advisory")),),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(query="patristics"), context)),
            ("alpha2020",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(reference_type="journal-article"), context)),
            ("beta2021",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(tag="history"), context)),
            ("beta2021",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(use="cited"), context)),
            ("beta2021",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(use="source-notes"), context)),
            ("alpha2020",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(integrity="warning"), context)),
            ("gamma2019",),
        )
        self.assertEqual(
            tuple(item.key for item in project_references(records, BibliographyFilters(sort="year"), context)),
            ("gamma2019", "alpha2020", "beta2021"),
        )

    def test_file_filter_distinguishes_present_missing_and_unset(self):
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp, "paper.pdf")
            present.write_text("x", encoding="utf-8")
            records = self.records(str(present)) + (
                ReferenceRecord(key="missing", title="Missing", file_path=str(Path(tmp, "none.pdf"))),
            )
            self.assertEqual(
                tuple(item.key for item in project_references(records, BibliographyFilters(file="present"))),
                ("alpha2020",),
            )
            self.assertEqual(
                tuple(item.key for item in project_references(records, BibliographyFilters(file="missing"))),
                ("missing",),
            )
            self.assertEqual(
                {item.key for item in project_references(records, BibliographyFilters(file="unset"))},
                {"beta2021", "gamma2019"},
            )

    def test_context_derives_citations_notes_sets_and_integrity_without_persistence(self):
        records = self.records()
        notes = (SourceNote(id="note-1", kind="quote", text="Quoted", reference_key="alpha2020"),)
        sets = (ReferenceSet("Core sources", members=("beta2021",)),)
        context = build_bibliography_context(
            records,
            document_text="Text [@beta2021, p. 2].",
            source_notes=notes,
            reference_sets=sets,
        )
        self.assertEqual(context.cited_keys, frozenset({"beta2021"}))
        self.assertEqual(context.source_note_keys, frozenset({"alpha2020"}))
        self.assertEqual(context.set_names("beta2021"), ("Core sources",))
        self.assertIn("warning", context.severities("gamma2019"))
        self.assertIn("advisory", context.severities("gamma2019"))

    def test_duplicate_generates_new_key_and_never_copies_aliases(self):
        record = ReferenceRecord(
            key="rossi2020alpha", title="Alpha", authors=("Rossi, Anna",),
            year="2020", aliases=("legacy",), extra_fields=(("X", "Y"),),
        )
        duplicate = duplicate_reference(record, record.identity_keys)
        self.assertNotEqual(duplicate.key, record.key)
        self.assertEqual(duplicate.aliases, ())
        self.assertEqual(duplicate.extra_fields, record.extra_fields)

    def test_safe_delete_impact_counts_all_known_authorities(self):
        records = (
            ReferenceRecord(key="alpha", title="Alpha", aliases=("oldalpha",)),
            ReferenceRecord(key="beta", title="Beta", extra_fields=(("Related Keys", "alpha"),)),
        )
        notes = (SourceNote(id="n1", kind="quote", text="Quote", reference_key="oldalpha"),)
        sets = (ReferenceSet("Set A", members=("alpha",)),)
        impact = build_delete_impact(
            records,
            "alpha",
            document_text="[@alpha] and [@oldalpha]",
            source_notes=notes,
            reference_sets=sets,
        )
        self.assertEqual(impact.citation_occurrences, 2)
        self.assertEqual(impact.source_note_occurrences, 1)
        self.assertEqual(impact.related_reference_owners, ("beta",))
        self.assertEqual(impact.reference_set_names, ("Set A",))
        self.assertTrue(impact.used)

    def test_detail_and_simple_exports_are_deterministic_derivations(self):
        record = self.records()[0]
        context = BibliographyContext(
            source_note_keys=frozenset({record.key}),
            set_names_by_key=((record.key, ("Core",)),),
        )
        detail = format_reference_detail(record, context)
        self.assertIn("Key: alpha2020", detail)
        self.assertIn("Reference Sets: Core", detail)
        self.assertIn("Source Notes: used", detail)
        plain = render_plain_bibliography((record,))
        markdown = render_markdown_bibliography((record,))
        self.assertIn("Rossi, Anna (2020). Alpha Book.", plain)
        self.assertTrue(markdown.startswith("# Bibliography\n\n- "))


if __name__ == "__main__":
    unittest.main()
