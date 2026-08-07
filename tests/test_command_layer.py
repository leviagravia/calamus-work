import unittest

from calamus_command_context import CommandContext, CommandInputError, CommandResult
from calamus_command_layer import CommandLayer
from calamus_command_registry import (
    CommandAvailability, CommandBinding, CommandRegistry, CommandShortcut, CommandSpec, shortcut_conflicts,
)


class CommandContextTests(unittest.TestCase):
    def test_context_is_small_copyable_and_has_no_app(self):
        ctx = CommandContext(source="test", data={"a": 1})
        self.assertEqual(ctx.get("a"), 1)
        newer = ctx.with_data(b=2)
        self.assertEqual(newer.data, {"a": 1, "b": 2})
        self.assertFalse(hasattr(ctx, "app"))


class CommandRegistryTests(unittest.TestCase):
    def test_register_lookup_shortcuts_and_sorted_listing(self):
        spec = CommandSpec(
            "writing.sort-lines", "Sort Lines", menu_path="Writing",
            shortcuts=(CommandShortcut("<Control><Shift>S", "Ctrl+Shift+S"),),
        )
        registry = CommandRegistry([spec, CommandSpec("writing.stats", "Statistics")])
        self.assertEqual(registry.require("writing.sort-lines").shortcut, "<Control><Shift>S")
        self.assertEqual(registry.command_ids(), ("writing.sort-lines", "writing.stats"))

    def test_metadata_contains_no_handler_or_enabled_state(self):
        spec = CommandSpec("writing.stats", "Statistics")
        self.assertFalse(hasattr(spec, "handler"))
        self.assertFalse(hasattr(spec, "enabled"))

    def test_duplicate_and_invalid_specs_are_rejected(self):
        registry = CommandRegistry([CommandSpec("writing.stats", "Statistics")])
        with self.assertRaises(ValueError):
            registry.register(CommandSpec("writing.stats", "Duplicate"))
        with self.assertRaises(ValueError):
            CommandSpec("Bad ID", "Bad")
        with self.assertRaises(ValueError):
            CommandSpec("ok.id", "")

    def test_shortcut_conflict_detection_reads_all_shortcuts(self):
        specs = [
            CommandSpec("a.one", "One", shortcuts=(CommandShortcut("<Ctrl>A"),)),
            CommandSpec("a.two", "Two", shortcuts=(CommandShortcut("<Control>A"),)),
        ]
        self.assertEqual(shortcut_conflicts(specs), {"<Control>A": ["a.one", "a.two"]})


class CommandLayerTests(unittest.TestCase):
    def test_explicit_binding_is_separate_from_metadata(self):
        layer = CommandLayer(CommandRegistry([CommandSpec("writing.demo", "Demo")]))
        layer.bind(CommandBinding("writing.demo", lambda ctx: CommandResult.ok(value=ctx.get("value"))))
        result = layer.dispatch("writing.demo", CommandContext(data={"value": 42}))
        self.assertTrue(result.success)
        self.assertEqual(result.value, 42)

    def test_unknown_unbound_and_disabled_are_fail_closed(self):
        registry = CommandRegistry([CommandSpec("writing.demo", "Demo")])
        availability = CommandAvailability()
        layer = CommandLayer(registry, availability=availability)
        self.assertFalse(layer.dispatch("missing.command").success)
        self.assertTrue(layer.dispatch("writing.demo").success)
        availability.set_enabled("writing.demo", False)
        self.assertFalse(layer.dispatch("writing.demo").success)

    def test_duplicate_binding_is_rejected(self):
        layer = CommandLayer(CommandRegistry([CommandSpec("writing.demo", "Demo")]))
        layer.bind_callable("writing.demo", lambda _ctx: True)
        with self.assertRaises(ValueError):
            layer.bind_callable("writing.demo", lambda _ctx: False)

    def test_expected_input_error_is_structured_but_programmer_error_propagates(self):
        registry = CommandRegistry([CommandSpec("a.input", "Input"), CommandSpec("a.bug", "Bug")])
        layer = CommandLayer(registry)
        layer.bind_callable("a.input", lambda _ctx: (_ for _ in ()).throw(CommandInputError("bad")))
        layer.bind_callable("a.bug", lambda _ctx: (_ for _ in ()).throw(RuntimeError("boom")))
        result = layer.dispatch("a.input")
        self.assertFalse(result.success)
        self.assertIsInstance(result.error, CommandInputError)
        with self.assertRaisesRegex(RuntimeError, "boom"):
            layer.dispatch("a.bug")


if __name__ == "__main__":
    unittest.main()
