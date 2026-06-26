import unittest

from calamus_command_context import CommandContext, CommandResult
from calamus_command_layer import CommandLayer
from calamus_command_registry import CommandRegistry, CommandSpec, shortcut_conflicts


class CommandContextTests(unittest.TestCase):
    def test_context_is_small_and_copyable(self):
        ctx = CommandContext(source="test", data={"a": 1})
        self.assertEqual(ctx.get("a"), 1)
        self.assertEqual(ctx.get("missing", "fallback"), "fallback")

        newer = ctx.with_data(b=2)
        self.assertEqual(ctx.get("b"), None)
        self.assertEqual(newer.get("a"), 1)
        self.assertEqual(newer.get("b"), 2)
        self.assertEqual(newer.source, "test")


class CommandResultTests(unittest.TestCase):
    def test_result_constructors(self):
        ok = CommandResult.ok("done", changed=True, value=3)
        self.assertTrue(ok.success)
        self.assertTrue(ok.changed)
        self.assertEqual(ok.value, 3)

        noop = CommandResult.noop()
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)

        fail = CommandResult.fail("bad")
        self.assertFalse(fail.success)
        self.assertEqual(fail.message, "bad")


class CommandRegistryTests(unittest.TestCase):
    def test_register_lookup_and_sorted_listing(self):
        registry = CommandRegistry()
        registry.register(CommandSpec("writing.sort-lines", "Sort Lines", menu_path="Writing", shortcut="<Control><Shift>S"))
        registry.register(CommandSpec("writing.stats", "Statistics", menu_path="Writing"))

        self.assertIn("writing.sort-lines", registry)
        self.assertEqual(registry.require("writing.stats").label, "Statistics")
        self.assertEqual(registry.command_ids(), ("writing.sort-lines", "writing.stats"))
        self.assertEqual(len(registry.list_commands()), 2)

    def test_duplicate_ids_are_rejected(self):
        registry = CommandRegistry([CommandSpec("writing.stats", "Statistics")])
        with self.assertRaises(ValueError):
            registry.register(CommandSpec("writing.stats", "Statistics Duplicate"))

    def test_invalid_specs_are_rejected(self):
        with self.assertRaises(ValueError):
            CommandSpec("", "Missing ID")
        with self.assertRaises(ValueError):
            CommandSpec("Bad ID", "Bad ID")
        with self.assertRaises(ValueError):
            CommandSpec("ok.id", "")
        with self.assertRaises(ValueError):
            CommandSpec("ok.id", "Bad Risk", risk_class="unknown")

    def test_shortcut_conflict_detection(self):
        specs = [
            CommandSpec("a.one", "One", shortcut="<Ctrl>A"),
            CommandSpec("a.two", "Two", shortcut="<Control>A"),
            CommandSpec("a.three", "Three", shortcut="<Control>B"),
        ]
        conflicts = shortcut_conflicts(specs)
        self.assertEqual(conflicts, {"<Control>A": ["a.one", "a.two"]})


class CommandLayerTests(unittest.TestCase):
    def test_dispatch_unknown_command_fails_safely(self):
        layer = CommandLayer()
        result = layer.dispatch("missing.command")
        self.assertFalse(result.success)
        self.assertIn("Unknown command", result.message)

    def test_dispatch_unwired_command_is_noop(self):
        layer = CommandLayer(CommandRegistry([CommandSpec("writing.stats", "Statistics")]))
        result = layer.dispatch("writing.stats")
        self.assertTrue(result.success)
        self.assertFalse(result.changed)
        self.assertIn("no handler", result.message)

    def test_dispatch_handler_result(self):
        def handler(ctx):
            return CommandResult.ok("handled", changed=True, value=ctx.get("value"))

        layer = CommandLayer()
        layer.register(CommandSpec("writing.demo", "Demo", handler=handler))
        result = layer.dispatch("writing.demo", CommandContext(data={"value": 42}))

        self.assertTrue(result.success)
        self.assertTrue(result.changed)
        self.assertEqual(result.value, 42)

    def test_dispatch_plain_handler_value_is_wrapped(self):
        layer = CommandLayer()
        layer.register(CommandSpec("writing.value", "Value", handler=lambda ctx: "plain"))
        result = layer.dispatch("writing.value")

        self.assertTrue(result.success)
        self.assertEqual(result.value, "plain")

    def test_dispatch_handler_exception_is_structured_failure(self):
        def broken(ctx):
            raise RuntimeError("boom")

        layer = CommandLayer()
        layer.register(CommandSpec("writing.broken", "Broken", handler=broken))
        result = layer.dispatch("writing.broken")

        self.assertFalse(result.success)
        self.assertIn("Command failed", result.message)
        self.assertIsInstance(result.error, RuntimeError)


if __name__ == "__main__":
    unittest.main()
