import unittest

from calamus_related_references import (
    plan_related_references_update,
    related_keys,
    related_reference_issues,
    replace_related_identity,
    with_related_keys,
)
from calamus_reference_store import parse_references_markdown, serialize_references_markdown
from calamus_references import ReferenceRecord


class RelatedReferencesTests(unittest.TestCase):
    def record(self, key, *, aliases=(), related=()):
        extras = (("Related Keys", ", ".join(related)),) if related else ()
        return ReferenceRecord(key=key, title=key.title(), aliases=aliases, extra_fields=extras)

    def test_canonical_field_roundtrip_preserves_other_extras(self):
        record = ReferenceRecord(
            key="a",
            title="A",
            extra_fields=(("Custom", "keep"), ("Related", "b; c"), ("Other", "value")),
        )
        updated = with_related_keys(record, ("c", "b", "c"))
        self.assertEqual(related_keys(updated), ("c", "b"))
        self.assertEqual(
            updated.extra_fields,
            (("Custom", "keep"), ("Related Keys", "c, b"), ("Other", "value")),
        )
        text = serialize_references_markdown((updated, self.record("b"), self.record("c")))
        parsed, diagnostics = parse_references_markdown(text)
        self.assertEqual(diagnostics, ())
        self.assertEqual(related_keys(parsed[0]), ("c", "b"))
        self.assertIn(("Custom", "keep"), parsed[0].extra_fields)

    def test_plan_adds_and_removes_both_relation_endpoints(self):
        a = self.record("a")
        b = self.record("b", aliases=("old-b",))
        c = self.record("c", related=("a",))
        plan = plan_related_references_update((a, b, c), "a", ("old-b",))
        self.assertEqual(plan.related_before, ("c",))
        self.assertEqual(plan.related_after, ("b",))
        self.assertEqual(plan.added, ("b",))
        self.assertEqual(plan.removed, ("c",))
        by_key = {record.key: record for record in plan.records_after}
        self.assertEqual(related_keys(by_key["a"]), ("b",))
        self.assertEqual(related_keys(by_key["b"]), ("a",))
        self.assertEqual(related_keys(by_key["c"]), ())
        self.assertEqual(set(plan.changed_record_keys), {"a", "b", "c"})

    def test_plan_rejects_self_missing_and_ambiguous_identities(self):
        records = (self.record("a"), self.record("b", aliases=("shared",)), self.record("c", aliases=("shared",)))
        with self.assertRaisesRegex(ValueError, "itself"):
            plan_related_references_update(records, "a", ("a",))
        with self.assertRaisesRegex(ValueError, "missing"):
            plan_related_references_update(records, "a", ("lost",))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            plan_related_references_update(records, "a", ("shared",))

    def test_integrity_detects_duplicate_self_missing_alias_and_asymmetry(self):
        a = ReferenceRecord(
            key="a",
            title="A",
            extra_fields=(("Related Keys", "a, old-b, old-b, missing"),),
        )
        b = self.record("b", aliases=("old-b",))
        issues = related_reference_issues((a, b))
        kinds = {issue.kind for issue in issues}
        self.assertIn("related-key-self", kinds)
        self.assertIn("related-key-uses-alias", kinds)
        self.assertIn("duplicate-related-key", kinds)
        self.assertIn("related-key-missing", kinds)
        self.assertIn("related-key-asymmetric", kinds)

    def test_key_replacement_is_canonical_and_counted(self):
        record = ReferenceRecord(
            key="a",
            title="A",
            extra_fields=(("Related", "old; old, other"),),
        )
        updated, count = replace_related_identity(record, "old", "new")
        self.assertEqual(count, 2)
        self.assertEqual(related_keys(updated), ("new", "other"))
        self.assertEqual(updated.extra_fields, (("Related Keys", "new, other"),))


if __name__ == "__main__":
    unittest.main()
