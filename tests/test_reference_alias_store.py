import unittest

from calamus_reference_store import parse_references_markdown, serialize_references_markdown
from calamus_references import ReferenceRecord


class ReferenceAliasStoreTests(unittest.TestCase):
    def test_aliases_roundtrip_as_markdown_and_are_deduplicated(self):
        record = ReferenceRecord(
            key="new2026",
            title="Title",
            aliases=("old2020", "old2020", "older2019"),
        )
        encoded = serialize_references_markdown((record,))
        self.assertIn("Aliases: old2020, older2019", encoded)
        records, diagnostics = parse_references_markdown(encoded)
        self.assertEqual(diagnostics, ())
        self.assertEqual(records, (record,))

    def test_primary_alias_and_cross_record_alias_collisions_are_blocking(self):
        text = """# Calamus References v1

## alpha
Title: Alpha
Aliases: legacy

## beta
Title: Beta
Aliases: alpha, legacy
"""
        records, diagnostics = parse_references_markdown(text)
        self.assertEqual(tuple(record.key for record in records), ("alpha", "beta"))
        messages = "\n".join(item.message for item in diagnostics)
        self.assertIn("identity alpha", messages)
        self.assertIn("identity legacy", messages)

    def test_alias_must_be_valid_and_cannot_equal_primary(self):
        with self.assertRaises(ValueError):
            ReferenceRecord(key="alpha", title="Alpha", aliases=("bad key",))
        with self.assertRaises(ValueError):
            ReferenceRecord(key="alpha", title="Alpha", aliases=("alpha",))

    def test_with_key_preserves_old_key_and_promotes_existing_alias(self):
        record = ReferenceRecord(
            key="alpha",
            title="Alpha",
            aliases=("legacy", "older"),
        )
        changed = record.with_key("legacy")
        self.assertEqual(changed.key, "legacy")
        self.assertEqual(changed.aliases, ("older", "alpha"))


if __name__ == "__main__":
    unittest.main()
