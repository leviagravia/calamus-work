import unittest
from datetime import datetime

from calamus_command_catalog import (
    LOW_RISK_COMMANDS, LOW_RISK_COMMAND_IDS, build_command_registry,
    build_low_risk_registry, build_pure_command_layer, command_specs, low_risk_command_specs,
)
from calamus_command_context import CommandContext
from calamus_command_handlers import handled_command_ids
from calamus_command_registry import CommandSpec, shortcut_conflicts

EXPECTED_COMMAND_IDS = (
    "edit.lowercase", "edit.uppercase", "writing.clean-pdf", "writing.insert-date-time",
    "writing.join-lines", "writing.reflow-paragraph", "writing.remove-extra-spaces",
    "writing.remove-trailing-spaces", "writing.sentence-case", "writing.smart-typography",
    "writing.sort-lines", "writing.statistics", "writing.title-case",
)

class CommandCatalogTests(unittest.TestCase):
    def test_low_risk_ids_are_preserved_but_metadata_has_no_handler(self):
        self.assertEqual(LOW_RISK_COMMAND_IDS, EXPECTED_COMMAND_IDS)
        self.assertIs(low_risk_command_specs(), LOW_RISK_COMMANDS)
        self.assertTrue(all(isinstance(spec, CommandSpec) for spec in LOW_RISK_COMMANDS))
        self.assertTrue(all(not hasattr(spec, "handler") for spec in LOW_RISK_COMMANDS))

    def test_full_catalog_is_single_unique_authority(self):
        specs = command_specs()
        registry = build_command_registry()
        self.assertGreaterEqual(len(specs), 110)
        self.assertEqual(len(specs), len(registry))
        self.assertEqual(len(specs), len({spec.command_id for spec in specs}))
        self.assertEqual(build_low_risk_registry().command_ids(), EXPECTED_COMMAND_IDS)

    def test_pure_handlers_are_explicit_bindings(self):
        self.assertEqual(handled_command_ids(), EXPECTED_COMMAND_IDS)
        layer = build_pure_command_layer()
        self.assertEqual(layer.binding_ids(), EXPECTED_COMMAND_IDS)
        result = layer.dispatch("edit.uppercase", CommandContext(source="test", data={"text": "abc"}))
        self.assertTrue(result.success)
        self.assertEqual(result.value, {"text": "ABC"})

    def test_time_handler_still_deterministic(self):
        layer = build_pure_command_layer()
        result = layer.dispatch("writing.insert-date-time", CommandContext(source="test", data={"now": datetime(2026,7,12,19,5)}))
        self.assertEqual(result.value, {"text": "2026-07-12 19:05"})

    def test_actual_default_shortcuts_have_no_conflicts(self):
        self.assertEqual(shortcut_conflicts(command_specs()), {})

if __name__ == "__main__": unittest.main()
