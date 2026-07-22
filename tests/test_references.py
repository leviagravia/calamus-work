import unittest

from calamus_references import (
    ReferenceRecord,
    is_valid_reference_key,
    suggest_reference_key,
)


class ReferenceRecordTests(unittest.TestCase):
    def test_record_normalizes_and_exposes_search_text(self):
        record = ReferenceRecord(
            key="  ratzinger1968introduction  ",
            title="  Introduction to Christianity  ",
            authors=("Ratzinger, Joseph", "Ratzinger, Joseph", ""),
            year=" 1968 ",
            tags=("faith", "faith", "christology"),
            annotation="General note",
        )
        self.assertEqual(record.key, "ratzinger1968introduction")
        self.assertEqual(record.authors, ("Ratzinger, Joseph",))
        self.assertEqual(record.tags, ("faith", "christology"))
        self.assertIn("ratzinger, joseph", record.search_text)
        self.assertIn("general note", record.search_text)
        self.assertEqual(record.author_year, "Ratzinger, Joseph, 1968")

    def test_invalid_key_and_empty_title_are_rejected(self):
        self.assertFalse(is_valid_reference_key("bad key"))
        with self.assertRaises(ValueError):
            ReferenceRecord(key="bad key", title="Title")
        with self.assertRaises(ValueError):
            ReferenceRecord(key="good-key", title="")

    def test_unknown_type_is_preserved_for_forward_compatibility(self):
        record = ReferenceRecord(key="sample2020", title="Sample", type="patent")
        self.assertEqual(record.type, "patent")

    def test_suggest_key_is_readable_ascii_and_disambiguated(self):
        key = suggest_reference_key(
            ["de Lubac, Henri"],
            "1944",
            "Corpus Mysticum",
            (),
        )
        self.assertEqual(key, "delubac1944corpus")
        duplicate = suggest_reference_key(
            ["de Lubac, Henri"],
            "1944",
            "Corpus Mysticum",
            {key},
        )
        self.assertEqual(duplicate, "delubac1944corpus-a")


if __name__ == "__main__":
    unittest.main()
