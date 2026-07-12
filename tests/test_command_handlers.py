import unittest
from datetime import datetime

from calamus_command_catalog import build_low_risk_registry, low_risk_command_specs
from calamus_command_context import CommandContext
from calamus_command_handlers import handle_insert_date_time, handle_sort_lines, handled_command_ids
from calamus_command_layer import CommandLayer
from calamus_writing import (
    clean_pdf_text,
    document_statistics,
    join_lines,
    reflow_paragraph,
    remove_extra_spaces,
    remove_trailing_spaces,
    sentence_case,
    smart_typography,
    sort_lines,
    title_case,
)


EXPECTED_HANDLED_COMMAND_IDS = (
    "edit.lowercase",
    "edit.uppercase",
    "writing.clean-pdf",
    "writing.insert-date-time",
    "writing.join-lines",
    "writing.reflow-paragraph",
    "writing.remove-extra-spaces",
    "writing.remove-trailing-spaces",
    "writing.sentence-case",
    "writing.smart-typography",
    "writing.sort-lines",
    "writing.statistics",
    "writing.title-case",
)


class PureCommandHandlerTests(unittest.TestCase):
    def setUp(self):
        self.layer = CommandLayer(build_low_risk_registry())

    def dispatch_text(self, command_id, text, **data):
        ctx = CommandContext(source="test", data={"text": text, **data})
        result = self.layer.dispatch(command_id, ctx)
        self.assertTrue(result.success, result.message)
        return result

    def assert_text_handler(self, command_id, text, expected):
        result = self.dispatch_text(command_id, text)
        self.assertEqual(result.value, {"text": expected})
        self.assertEqual(result.changed, expected != text)

    def test_handled_command_ids_are_explicit_and_stable(self):
        self.assertEqual(handled_command_ids(), EXPECTED_HANDLED_COMMAND_IDS)

    def test_catalog_attaches_handlers_only_to_pure_commands(self):
        specs = {spec.command_id: spec for spec in low_risk_command_specs()}

        for command_id in EXPECTED_HANDLED_COMMAND_IDS:
            self.assertIsNotNone(specs[command_id].handler)
            self.assertIn("pure-handler", specs[command_id].flags)
            self.assertNotIn("metadata-only", specs[command_id].flags)

        self.assertIsNotNone(specs["writing.insert-date-time"].handler)
        self.assertIn("pure-handler", specs["writing.insert-date-time"].flags)
        self.assertNotIn("metadata-only", specs["writing.insert-date-time"].flags)

    def test_uppercase_lowercase_handlers(self):
        self.assert_text_handler("edit.uppercase", "Abc è", "ABC È")
        self.assert_text_handler("edit.lowercase", "AbC È", "abc è")

    def test_writing_handlers_match_existing_pure_functions(self):
        samples = {
            "writing.sort-lines": ("z\nb\na\n", sort_lines),
            "writing.clean-pdf": ("inter-\nrotto\n\nnuovo paragrafo", clean_pdf_text),
            "writing.remove-extra-spaces": ("a   b\t\tc", remove_extra_spaces),
            "writing.remove-trailing-spaces": ("a  \n b\t\n", remove_trailing_spaces),
            "writing.smart-typography": ('"ciao" -- test...', smart_typography),
            "writing.join-lines": ("a\nb\nc", join_lines),
            "writing.title-case": ("il nome della rosa", title_case),
            "writing.sentence-case": ("CIAO. MONDO", sentence_case),
        }

        for command_id, (text, function) in samples.items():
            with self.subTest(command_id=command_id):
                self.assert_text_handler(command_id, text, function(text))

    def test_sort_lines_handler_uses_reverse_from_context(self):
        text = "a\nc\nb\n"
        result = self.dispatch_text("writing.sort-lines", text, reverse=True)
        self.assertEqual(result.value, {"text": sort_lines(text, reverse=True)})
        self.assertTrue(result.changed)

    def test_sort_lines_handler_rejects_non_boolean_reverse(self):
        context = CommandContext(
            source="test", data={"text": "b\na", "reverse": 1}
        )
        with self.assertRaisesRegex(TypeError, "reverse.*boolean"):
            handle_sort_lines(context)

        result = self.layer.dispatch("writing.sort-lines", context)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "Command failed: writing.sort-lines")

    def test_reflow_handler_uses_width_from_context(self):
        text = "uno due tre quattro cinque sei sette otto"
        result = self.dispatch_text("writing.reflow-paragraph", text, width=12)
        self.assertEqual(result.value, {"text": reflow_paragraph(text, width=12)})

    def test_statistics_handler_is_read_only(self):
        text = "uno due\n\ntré"
        result = self.dispatch_text("writing.statistics", text)

        self.assertTrue(result.success)
        self.assertFalse(result.changed)
        self.assertEqual(result.value, {"statistics": document_statistics(text)})

    def test_insert_date_time_formats_explicit_moment(self):
        now = datetime(2026, 7, 12, 19, 5)
        result = self.layer.dispatch(
            "writing.insert-date-time",
            CommandContext(source="test", data={"now": now}),
        )
        self.assertTrue(result.success)
        self.assertTrue(result.changed)
        self.assertEqual(result.value, {"text": "2026-07-12 19:05"})

    def test_insert_date_time_uses_explicit_format(self):
        now = datetime(2026, 7, 12, 19, 5, 9)
        result = self.layer.dispatch(
            "writing.insert-date-time",
            CommandContext(source="test", data={"now": now, "format": "%d/%m/%Y %H:%M:%S"}),
        )
        self.assertTrue(result.success)
        self.assertEqual(result.value, {"text": "12/07/2026 19:05:09"})

    def test_insert_date_time_rejects_missing_or_invalid_context(self):
        missing = self.layer.dispatch(
            "writing.insert-date-time", CommandContext(source="test")
        )
        self.assertFalse(missing.success)
        with self.assertRaisesRegex(TypeError, "now.*datetime"):
            handle_insert_date_time(
                CommandContext(source="test", data={"now": "2026-07-12"})
            )
        invalid_format = self.layer.dispatch(
            "writing.insert-date-time",
            CommandContext(source="test", data={"now": datetime(2026, 7, 12), "format": 123}),
        )
        self.assertFalse(invalid_format.success)

    def test_missing_or_empty_text_is_safe(self):
        result = self.layer.dispatch("edit.uppercase", CommandContext(source="test"))
        self.assertTrue(result.success)
        self.assertEqual(result.value, {"text": ""})
        self.assertFalse(result.changed)

    def test_non_string_text_fails_as_structured_error(self):
        result = self.layer.dispatch("edit.uppercase", CommandContext(source="test", data={"text": 123}))
        self.assertFalse(result.success)
        self.assertIn("Command failed", result.message)


if __name__ == "__main__":
    unittest.main()
