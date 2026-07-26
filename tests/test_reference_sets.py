import os
import tempfile
import unittest

from calamus_reference_set_store import MarkdownReferenceSetStore
from calamus_reference_sets import (
    ReferenceSet,
    canonicalize_reference_set,
    parse_reference_sets_markdown,
    reference_set_issues,
    replace_reference_set_member,
    serialize_reference_sets_markdown,
)
from calamus_references import ReferenceRecord


class ReferenceSetModelTests(unittest.TestCase):
    def setUp(self):
        self.records = (
            ReferenceRecord(key="a", title="A", aliases=("old-a",)),
            ReferenceRecord(key="b", title="B"),
        )

    def test_roundtrip_is_deterministic_and_transparent(self):
        sets = (
            ReferenceSet("Core sources", "Primary sources.", ("a", "b")),
            ReferenceSet("Background", "", ("b",)),
        )
        text = serialize_reference_sets_markdown(sets)
        self.assertEqual(text.splitlines()[0], "# Calamus Reference Sets v1")
        self.assertIn("## Core sources", text)
        self.assertIn("- a", text)
        parsed, diagnostics = parse_reference_sets_markdown(text)
        self.assertEqual(diagnostics, ())
        self.assertEqual(parsed, sets)
        self.assertEqual(serialize_reference_sets_markdown(parsed), text)

    def test_unicode_names_and_descriptions_roundtrip_in_utf8(self):
        sets = (ReferenceSet("Fonti per la Chiesa", "Tradizione, Église e δογματική.", ("a",)),)
        text = serialize_reference_sets_markdown(sets)
        parsed, diagnostics = parse_reference_sets_markdown(text)
        self.assertEqual(diagnostics, ())
        self.assertEqual(parsed, sets)
        self.assertIn("Église", text)
        self.assertIn("δογματική", text)

    def test_name_case_is_preserved_exactly_across_serialize_parse_and_store(self):
        original = ReferenceSet("Core sources", "Primary works.", ("a", "b"))
        text = serialize_reference_sets_markdown((original,))
        self.assertIn("## Core sources\n", text)
        self.assertNotIn("## Core Sources\n", text)
        parsed, diagnostics = parse_reference_sets_markdown(text)
        self.assertEqual(diagnostics, ())
        self.assertEqual(parsed[0].name, "Core sources")

        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "reference-sets.md")
            store = MarkdownReferenceSetStore(path)
            result = store.save((original,), store.load().token)
            self.assertTrue(result.saved)
            reopened = store.load()
            self.assertEqual(reopened.diagnostics, ())
            self.assertEqual(reopened.sets[0].name, "Core sources")
            with open(path, "r", encoding="utf-8") as handle:
                stored_heading = handle.read().splitlines()[2]
            self.assertEqual(stored_heading, "## Core sources")

    def test_parser_reports_malformed_and_duplicate_content(self):
        text = (
            "# Calamus Reference Sets v1\n\n"
            "## Core\n\nDescription: One\nDescription: Two\n\n- a\n- a\n"
            "unexpected\n\n## core\n\n- b\n"
        )
        sets, diagnostics = parse_reference_sets_markdown(text)
        self.assertEqual(len(sets), 2)
        messages = "\n".join(item.message for item in diagnostics)
        self.assertIn("more than one Description", messages)
        self.assertIn("repeats member", messages)
        self.assertIn("Unrecognized", messages)
        self.assertIn("duplicated", messages)
        self.assertTrue(all(item.blocking for item in diagnostics))

    def test_aliases_are_accepted_only_as_input_and_canonicalized(self):
        item = canonicalize_reference_set(ReferenceSet("Set", members=("old-a", "b")), self.records)
        self.assertEqual(item.members, ("a", "b"))
        with self.assertRaisesRegex(ValueError, "missing"):
            canonicalize_reference_set(ReferenceSet("Set", members=("lost",)), self.records)

    def test_integrity_reports_alias_and_missing_members(self):
        issues = reference_set_issues(
            (ReferenceSet("Set", members=("old-a", "lost")),),
            self.records,
        )
        self.assertEqual(
            {issue.kind for issue in issues},
            {"reference-set-member-uses-alias", "reference-set-member-missing"},
        )

    def test_key_migration_rewrites_memberships(self):
        before = (ReferenceSet("Set", members=("a", "b")),)
        after, count = replace_reference_set_member(before, "a", "new-a")
        self.assertEqual(count, 1)
        self.assertEqual(after[0].members, ("new-a", "b"))


class ReferenceSetStoreTests(unittest.TestCase):
    def test_real_file_atomic_save_and_stale_token(self):
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, "reference-sets.md")
            store = MarkdownReferenceSetStore(path)
            empty = store.load()
            result = store.save((ReferenceSet("Core", members=("a",)),), empty.token)
            self.assertTrue(result.saved)
            self.assertEqual(store.load().sets[0].name, "Core")
            with open(path, "a", encoding="utf-8") as handle:
                handle.write("\n")
            conflict = store.save((), result.token)
            self.assertEqual(conflict.status, "conflict")


if __name__ == "__main__":
    unittest.main()
