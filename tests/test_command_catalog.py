import unittest

from calamus_command_catalog import LOW_RISK_COMMANDS, build_low_risk_registry, low_risk_command_specs
from calamus_command_context import CommandContext
from calamus_command_handlers import handled_command_ids
from calamus_command_layer import CommandLayer
from calamus_command_registry import CommandSpec, shortcut_conflicts


EXPECTED_COMMAND_IDS = (
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


class CommandCatalogTests(unittest.TestCase):
    def test_low_risk_specs_are_declared(self):
        specs = low_risk_command_specs()
        self.assertIs(specs, LOW_RISK_COMMANDS)
        self.assertGreaterEqual(len(specs), 10)
        self.assertTrue(all(isinstance(spec, CommandSpec) for spec in specs))

    def test_command_ids_are_stable_and_sorted_by_registry(self):
        registry = build_low_risk_registry()
        self.assertEqual(registry.command_ids(), EXPECTED_COMMAND_IDS)

    def test_all_registered_commands_are_low_risk(self):
        for spec in low_risk_command_specs():
            self.assertEqual(spec.risk_class, "low")
            self.assertTrue(spec.description)
            self.assertTrue(spec.menu_path)

    def test_pure_commands_have_handlers_but_time_command_does_not(self):
        handled = set(handled_command_ids())
        for spec in low_risk_command_specs():
            if spec.command_id in handled:
                self.assertIsNotNone(spec.handler)
                self.assertIn("pure-handler", spec.flags)
            else:
                self.assertEqual(spec.command_id, "writing.insert-date-time")
                self.assertIsNone(spec.handler)
                self.assertIn("metadata-only", spec.flags)

    def test_no_shortcut_conflicts_in_catalog(self):
        self.assertEqual(shortcut_conflicts(low_risk_command_specs()), {})

    def test_catalog_can_build_registry_without_duplicates(self):
        registry = build_low_risk_registry()
        self.assertEqual(len(registry), len(low_risk_command_specs()))
        self.assertIsNotNone(registry.get("writing.statistics"))

    def test_layer_dispatch_for_pure_command_is_operational_in_isolation(self):
        layer = CommandLayer(build_low_risk_registry())
        result = layer.dispatch("edit.uppercase", CommandContext(source="test", data={"text": "abc"}))

        self.assertTrue(result.success)
        self.assertTrue(result.changed)
        self.assertEqual(result.value, {"text": "ABC"})

    def test_layer_dispatch_for_time_command_remains_noop(self):
        layer = CommandLayer(build_low_risk_registry())
        result = layer.dispatch("writing.insert-date-time", CommandContext(source="test", data={"text": "abc"}))

        self.assertTrue(result.success)
        self.assertFalse(result.changed)
        self.assertIn("no handler", result.message)


if __name__ == "__main__":
    unittest.main()
