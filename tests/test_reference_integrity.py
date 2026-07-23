import unittest

from calamus_document_structure import build_document_structure
from calamus_reference_integrity import (
    build_identity_index,
    plan_reference_key_migration,
    resolve_reference,
    run_research_check,
)
from calamus_references import ReferenceRecord
from calamus_source_notes import SourceLocator, SourceNote


class ReferenceIntegrityTests(unittest.TestCase):
    def records(self):
        return (
            ReferenceRecord(
                key="newkey",
                title="One",
                authors=("Author, A",),
                year="2020",
                aliases=("oldkey",),
                doi="https://doi.org/10.1000/ABC",
            ),
            ReferenceRecord(
                key="second",
                title="Two",
                doi="10.1000/abc",
                extra_fields=(("Related Keys", "oldkey, missing"),),
            ),
        )

    def test_identity_resolution_distinguishes_primary_alias_and_missing(self):
        records = self.records()
        self.assertEqual(build_identity_index(records)["oldkey"], "newkey")
        self.assertEqual(resolve_reference(records, "newkey").status, "primary")
        alias = resolve_reference(records, "oldkey")
        self.assertEqual((alias.status, alias.canonical_key), ("alias", "newkey"))
        self.assertEqual(resolve_reference(records, "absent").status, "missing")

    def test_migration_rewrites_exact_active_citations_notes_and_related_keys(self):
        records = (
            ReferenceRecord(
                key="oldkey",
                title="One",
                extra_fields=(("Related Keys", "oldkey; other"),),
            ),
            ReferenceRecord(key="other", title="Other"),
        )
        text = "Use [@oldkey, p. 4] and @oldkey. `[@oldkey]`\n```\n@oldkey\n```\n"
        notes = (
            SourceNote(id="sn-1", kind="quote", text="Quote", reference_key="oldkey"),
        )
        plan = plan_reference_key_migration(records, text, notes, "oldkey", "newkey")
        self.assertEqual(plan.impact.citation_occurrences, 2)
        self.assertEqual(plan.impact.source_note_occurrences, 1)
        self.assertEqual(plan.impact.related_key_occurrences, 1)
        self.assertIn("[@newkey, p. 4]", plan.document_after)
        self.assertIn("`[@oldkey]`", plan.document_after)
        self.assertIn("\n@oldkey\n", plan.document_after)
        renamed = plan.candidate_records[0]
        self.assertEqual(renamed.key, "newkey")
        self.assertEqual(renamed.aliases, ("oldkey",))
        self.assertEqual(plan.source_notes_after[0].reference_key, "newkey")

    def test_migration_fails_closed_on_other_record_identity_collision(self):
        records = (
            ReferenceRecord(key="old", title="Old"),
            ReferenceRecord(key="other", title="Other", aliases=("taken",)),
        )
        with self.assertRaisesRegex(ValueError, "already exists"):
            plan_reference_key_migration(records, "", (), "old", "taken")

    def test_research_check_is_deterministic_and_reports_required_classes(self):
        records = self.records()
        text = "# Section {#section}\n[@oldkey] [@missing] [@newkey, p. 8]\n"
        notes = (
            SourceNote(
                id="sn-alias",
                kind="quote",
                text="Quote",
                reference_key="oldkey",
                target="#section",
            ),
            SourceNote(
                id="sn-missing",
                kind="paraphrase",
                text="Paraphrase",
                reference_key="absent",
                target="#absent",
                locator=SourceLocator(page="2"),
            ),
        )
        structure = build_document_structure(text)
        first = run_research_check(records, text, notes, structure)
        second = run_research_check(records, text, notes, structure)
        self.assertEqual(first, second)
        kinds = {issue.kind for issue in first.issues}
        self.assertTrue({
            "citation-uses-alias",
            "cited-key-missing",
            "duplicate-doi",
            "incomplete-reference",
            "related-key-uses-alias",
            "related-key-missing",
            "source-note-uses-alias",
            "source-note-reference-missing",
            "source-note-target-missing",
            "source-note-without-locator",
        }.issubset(kinds))
        self.assertGreater(first.error_count, 0)
        self.assertGreater(first.warning_count, 0)
        self.assertGreater(first.advisory_count, 0)


if __name__ == "__main__":
    unittest.main()
