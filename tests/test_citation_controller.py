import unittest

from calamus_citation_controller import CitationController
from calamus_references import ReferenceRecord


class CitationControllerTests(unittest.TestCase):
    def setUp(self):
        self.records = (
            ReferenceRecord(key="alpha2020", title="Alpha", authors=("Author, A",), year="2020"),
            ReferenceRecord(key="beta2021", title="Beta", authors=("Author, B",), year="2021"),
        )
        self.inserted = []
        self.shown = []
        self.errors = []
        self.choices = []
        self.controller = CitationController(
            reference_records_provider=lambda: self.records,
            insert_text=lambda text: (self.inserted.append(text), True)[1],
            show_reference=lambda key: (self.shown.append(key), True)[1],
            choose_key=lambda keys: self.choices.pop(0) if self.choices else None,
            on_error=self.errors.append,
        )

    def test_quick_cite_inserts_canonical_pandoc_syntax(self):
        self.assertTrue(self.controller.quick_cite("alpha2020", "p. 42"))
        self.assertEqual(self.inserted, ["[@alpha2020, p. 42]"])
        self.assertEqual(self.errors, [])

    def test_quick_cite_rejects_missing_reference(self):
        self.assertFalse(self.controller.quick_cite("missing2022"))
        self.assertEqual(self.inserted, [])
        self.assertIn("not available", self.errors[-1])

    def test_open_single_citation_selects_reference(self):
        text = "See [@alpha2020, p. 2]."
        self.assertTrue(self.controller.open_citation(text, text.index("alpha") + 1))
        self.assertEqual(self.shown, ["alpha2020"])

    def test_open_grouped_citation_uses_key_under_cursor(self):
        text = "See [@alpha2020; @beta2021]."
        self.assertTrue(self.controller.open_citation(text, text.index("beta") + 1))
        self.assertEqual(self.shown, ["beta2021"])
        self.assertEqual(self.choices, [])

    def test_open_grouped_citation_between_keys_requests_choice(self):
        text = "See [@alpha2020; @beta2021]."
        self.choices.append("beta2021")
        self.assertTrue(self.controller.open_citation(text, text.index(";")))
        self.assertEqual(self.shown, ["beta2021"])

    def test_cancelled_ambiguous_choice_is_noop(self):
        text = "See [@alpha2020; @beta2021]."
        self.assertFalse(self.controller.open_citation(text, text.index(";")))
        self.assertEqual(self.shown, [])
        self.assertEqual(self.errors, [])

    def test_missing_library_key_is_reported(self):
        text = "See [@missing2022]."
        self.assertFalse(self.controller.open_citation(text, text.index("missing") + 1))
        self.assertIn("missing from References", self.errors[-1])

    def test_cursor_outside_citation_is_reported(self):
        self.assertFalse(self.controller.open_citation("plain text", 2))
        self.assertIn("Place the cursor", self.errors[-1])

    def test_failed_insert_is_reported(self):
        controller = CitationController(
            reference_records_provider=lambda: self.records,
            insert_text=lambda _text: False,
            show_reference=lambda _key: True,
            choose_key=lambda _keys: None,
            on_error=self.errors.append,
        )
        self.assertFalse(controller.quick_cite("alpha2020"))
        self.assertIn("could not be inserted", self.errors[-1])

    def test_alias_lookup_selects_canonical_and_quick_cite_emits_primary_key(self):
        records = (ReferenceRecord(key="current", title="Current", aliases=("legacy",)),)
        inserted = []
        shown = []
        controller = CitationController(
            reference_records_provider=lambda: records,
            insert_text=lambda text: inserted.append(text) or True,
            show_reference=lambda key: shown.append(key) or True,
            choose_key=lambda keys: keys[0],
            on_error=self.errors.append,
        )
        self.assertTrue(controller.quick_cite("legacy"))
        self.assertEqual(inserted, ["[@current]"])
        self.assertTrue(controller.open_citation("See [@legacy].", 7))
        self.assertEqual(shown, ["current"])

    def test_provider_must_return_records(self):
        controller = CitationController(
            reference_records_provider=lambda: ("alpha2020",),
            insert_text=lambda _text: True,
            show_reference=lambda _key: True,
            choose_key=lambda _keys: None,
            on_error=self.errors.append,
        )
        with self.assertRaises(TypeError):
            _ = controller.records


if __name__ == "__main__":
    unittest.main()
