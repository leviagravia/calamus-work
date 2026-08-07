from __future__ import annotations

import ast
from dataclasses import fields
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
CALAMUS = str(ROOT / "calamus")
if CALAMUS not in sys.path:
    sys.path.insert(0, CALAMUS)

from calamus_application_commands import (  # noqa: E402
    APPLICATION_METHOD_TARGETS,
    CHECK_COMMAND_IDS,
    build_application_command_layer,
)
from calamus_command_catalog import (  # noqa: E402
    LOW_RISK_COMMAND_IDS,
    command_specs,
    research_command_specs,
    shortcut_bindings,
    shortcut_guide_entries,
)
from calamus_command_context import CommandContext, CommandInputError  # noqa: E402
from calamus_command_layer import CommandLayer  # noqa: E402
from calamus_command_registry import (  # noqa: E402
    CommandAvailability,
    CommandBinding,
    CommandRegistry,
    CommandSpec,
)

BASELINE = "aa73cc830b2c2120e26fd7ffb5d21b56c95e709b"
EXPECTED_LOW_RISK = {
    "edit.lowercase", "edit.uppercase", "writing.clean-pdf",
    "writing.insert-date-time", "writing.join-lines", "writing.reflow-paragraph",
    "writing.remove-extra-spaces", "writing.remove-trailing-spaces",
    "writing.sentence-case", "writing.smart-typography", "writing.sort-lines",
    "writing.statistics", "writing.title-case",
}


class _FakeApp:
    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: True


class W104CommandActionContractTests(unittest.TestCase):
    def test_w104_is_preserved_under_current_w105_identity(self):
        version = (ROOT / "calamus/calamus_version.py").read_text(encoding="utf-8")
        self.assertIn('DEVELOPMENT_BUILD_LABEL = "Development build"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM = "W106"', version)
        self.assertIn('DEVELOPMENT_WORK_ITEM_DESCRIPTION = "Preferences and Application State Extraction"', version)
        self.assertIn(f'PUBLISHED_BASELINE = "{BASELINE}"', version)

    def test_catalog_is_single_stable_identity_authority(self):
        specs = command_specs()
        ids = [spec.command_id for spec in specs]
        self.assertEqual(len(specs), 118)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(LOW_RISK_COMMAND_IDS), EXPECTED_LOW_RISK)
        self.assertEqual(len(research_command_specs()), 26)

    def test_metadata_execution_and_availability_are_separate(self):
        names = {field.name for field in fields(CommandSpec)}
        self.assertNotIn("handler", names)
        self.assertNotIn("enabled", names)
        self.assertIn("shortcuts", names)
        registry = CommandRegistry((CommandSpec("test.command", "Test"),))
        availability = CommandAvailability()
        layer = CommandLayer(registry, availability=availability)
        calls = []
        layer.bind(CommandBinding("test.command", lambda ctx: calls.append(ctx.source) or 7))
        self.assertTrue(layer.dispatch("test.command", CommandContext(source="test")).success)
        self.assertEqual(calls, ["test"])
        availability.set_enabled("test.command", False)
        self.assertFalse(layer.dispatch("test.command").success)

    def test_context_has_no_whole_app_or_service_bag(self):
        names = {field.name for field in fields(CommandContext)}
        self.assertEqual(names, {"source", "data"})
        source = (ROOT / "calamus/calamus_command_context.py").read_text(encoding="utf-8")
        self.assertNotIn("app:", source)
        self.assertNotIn("services", source.casefold())
        launcher = (ROOT / "bin/calamus").read_text(encoding="utf-8")
        self.assertNotIn("CommandContext(app=self", launcher)

    def test_command_core_is_gtk_free(self):
        for rel in (
            "calamus/calamus_command_registry.py",
            "calamus/calamus_command_catalog.py",
            "calamus/calamus_command_context.py",
            "calamus/calamus_command_layer.py",
            "calamus/calamus_command_handlers.py",
        ):
            source = (ROOT / rel).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            self.assertFalse(any(name == "gi" or name.startswith("gi.") for name in imports), rel)
            for token in ("Gtk.", "Gdk.", "Pango.", "PangoCairo."):
                self.assertNotIn(token, source, rel)

    def test_shortcuts_and_guide_are_catalog_projections(self):
        bindings = shortcut_bindings()
        guides = shortcut_guide_entries()
        self.assertEqual(len(bindings), 77)
        self.assertEqual(len(guides), 94)
        self.assertEqual(len({accelerator for accelerator, _cid, _data in bindings}), 77)
        actual = {(a, cid, tuple(sorted(data.items()))) for a, cid, data in bindings}
        for required in (
            ("<Alt>Up", "edit.move-line", (("direction", -1),)),
            ("<Alt>Down", "edit.move-line", (("direction", 1),)),
            ("<Control>plus", "options.font-size.adjust", (("delta", 1),)),
            ("<Control>minus", "options.font-size.adjust", (("delta", -1),)),
            ("<Control>slash", "help.keyboard-shortcuts", ()),
            ("<Control>Page_Up", "navigate.heading.previous", ()),
            ("<Control>Page_Down", "navigate.heading.next", ()),
            ("<Control>Y", "edit.redo", ()),
            ("<Control><Shift>Z", "edit.redo", ()),
        ):
            self.assertIn(required, actual)
        shortcuts_source = (ROOT / "calamus/calamus_shortcuts.py").read_text(encoding="utf-8")
        self.assertIn("shortcut_guide_entries", shortcuts_source)
        self.assertNotIn('ShortcutSpec("File"', shortcuts_source)

    def test_application_bindings_are_explicit_and_almost_total(self):
        layer = build_application_command_layer(_FakeApp())
        catalog_ids = {spec.command_id for spec in command_specs()}
        binding_ids = set(layer.binding_ids())
        self.assertEqual(len(binding_ids), 117)
        self.assertEqual(catalog_ids - binding_ids, {"view.clip-wrap-auto"})
        source = (ROOT / "calamus/calamus_application_commands.py").read_text(encoding="utf-8")
        self.assertNotIn("getattr(app, command_id", source)
        self.assertNotIn("service locator", source.casefold())

    def test_menu_and_check_callbacks_use_stable_command_identity(self):
        ui = (ROOT / "calamus/calamus_ui.py").read_text(encoding="utf-8")
        model = (ROOT / "calamus/calamus_menu_model.py").read_text(encoding="utf-8")
        self.assertIn("class MenuGtkAdapter", ui)
        self.assertIn("self._invoke_command(", ui)
        self.assertIn('source="menu"', ui)
        self.assertIn('data={"active": bool(widget.get_active())}', ui)
        self.assertIn("command_shortcut_bindings()", ui)
        self.assertIn('MenuCommandSpec(command_id, label, kind="check")', model)
        self.assertNotIn("app.on_new()),", ui)
        self.assertEqual(set(CHECK_COMMAND_IDS.values()), {
            "options.appearance.dark", "options.line-numbers", "navigate.navigator-panel",
            "options.always-on-top", "options.appearance.light", "research.panel",
            "options.transparent-mode", "writing.typewriter-mode", "options.word-wrap",
            "navigate.workspace-panel",
        })
        for callback in (
            "on_new", "on_open", "on_save", "on_quit", "on_undo", "on_redo",
            "on_uppercase", "show_references", "show_tags", "on_system_info",
        ):
            self.assertIn(callback, APPLICATION_METHOD_TARGETS)

    def test_parameterized_dynamic_families_use_one_id_plus_payload(self):
        model = (ROOT / "calamus/calamus_menu_model.py").read_text(encoding="utf-8")
        application = (ROOT / "calamus/calamus_application_commands.py").read_text(encoding="utf-8")
        for command_id in (
            "file.template.open", "file.recent.open", "file.favourite.open",
            "file.workspace.recent.open", "options.opacity.set",
            "options.font-size.adjust",
        ):
            self.assertIn(command_id, model)
        self.assertIn("research.insert-clip-slot", application)
        self.assertIn("edit.move-line", application)
        self.assertIn("writing.sort-lines", application)

    def test_only_classified_input_failures_are_absorbed(self):
        registry = CommandRegistry((
            CommandSpec("test.input", "Input"),
            CommandSpec("test.bug", "Bug"),
        ))
        layer = CommandLayer(registry)
        layer.bind_callable("test.input", lambda _ctx: (_ for _ in ()).throw(CommandInputError("bad")))
        layer.bind_callable("test.bug", lambda _ctx: (_ for _ in ()).throw(RuntimeError("bug")))
        result = layer.dispatch("test.input")
        self.assertFalse(result.success)
        self.assertIsInstance(result.error, CommandInputError)
        with self.assertRaisesRegex(RuntimeError, "bug"):
            layer.dispatch("test.bug")

    def test_w105_extends_but_does_not_replace_w104_command_core(self):
        combined = "\n".join(
            (ROOT / rel).read_text(encoding="utf-8")
            for rel in (
                "calamus/calamus_command_registry.py",
                "calamus/calamus_command_catalog.py",
                "calamus/calamus_command_layer.py",
                "calamus/calamus_application_commands.py",
            )
        )
        self.assertNotIn("Gtk.", combined)
        self.assertNotIn("MenuGtkAdapter", combined)
        self.assertIn("class CommandAvailability", combined)
        state = (ROOT / "calamus/calamus_ui_state.py").read_text(encoding="utf-8")
        self.assertIn("self._availability.set_enabled(command_id, state.enabled)", state)


if __name__ == "__main__":
    unittest.main(verbosity=2)
