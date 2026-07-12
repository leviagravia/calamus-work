from pathlib import Path
import ast
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / "bin" / "calamus"
UI = ROOT / "calamus" / "calamus_ui.py"
sys.path.insert(0, str(ROOT / "calamus"))

from calamus_command_catalog import build_low_risk_registry
from calamus_command_context import CommandContext
from calamus_command_layer import CommandLayer
from calamus_writing import sentence_case


EXPECTED_DISPATCH_IDS = [
    "edit.lowercase",
    "edit.uppercase",
    "writing.clean-pdf",
    "writing.join-lines",
    "writing.reflow-paragraph",
    "writing.remove-extra-spaces",
    "writing.remove-trailing-spaces",
    "writing.sentence-case",
    "writing.smart-typography",
    "writing.sort-lines",
    "writing.statistics",
    "writing.title-case",
]


def app_methods():
    source = BIN.read_text(encoding="utf-8")
    tree = ast.parse(source)
    lines = source.splitlines()
    out = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "App":
            for child in node.body:
                if isinstance(child, ast.FunctionDef):
                    out[child.name] = "\n".join(lines[child.lineno - 1:child.end_lineno])
    return source, out


class SentenceCaseLayerWiringTests(unittest.TestCase):
    def test_menu_and_shortcut_use_one_explicit_entrypoint(self):
        ui = UI.read_text(encoding="utf-8")
        self.assertIn(
            'add_item(revisem, "Sentence case\\tCtrl+Alt+Shift+Y", app.on_sentence_case)',
            ui,
        )
        self.assertIn('("<Control><Alt><Shift>Y", app.on_sentence_case)', ui)
        self.assertEqual(ui.count("app.on_sentence_case"), 2)
        self.assertNotIn(
            'lambda *_: app.apply_text_transform(sentence_case, "Sentence Case")',
            ui,
        )

    def test_dispatch_surface_adds_only_sentence_case(self):
        source = BIN.read_text(encoding="utf-8")
        dispatch_ids = re.findall(r"\.dispatch\(\s*['\"]([^'\"]+)['\"]", source, flags=re.S)
        self.assertEqual(sorted(dispatch_ids), EXPECTED_DISPATCH_IDS)

    def test_helper_is_compute_only(self):
        _source, methods = app_methods()
        helper = methods["command_layer_sentence_case_text"]
        self.assertIn('"writing.sentence-case"', helper)
        self.assertIn(
            'CommandContext(app=self, source="gui", data={"text": text})',
            helper,
        )
        for forbidden in [
            ".delete(", ".insert(", "set_text(", "mark_modified",
            "finalize_command_edit", "execute_command", "begin_user_action",
            "end_user_action", "selected_or_all_range", "get_buffer",
            "Clipboard", "write_text_file",
        ]:
            self.assertNotIn(forbidden, helper)

    def test_apply_text_transform_routes_command_before_mutation(self):
        _source, methods = app_methods()
        apply = methods["apply_text_transform"]
        self.assertIn("use_layer_sentence_case", apply)
        self.assertIn('command_name == "Sentence Case"', apply)
        self.assertIn("transform is sentence_case", apply)
        self.assertIn("command_layer_sentence_case_text(old)", apply)
        branch_pos = apply.index("elif use_layer_sentence_case:")
        edit_pos = apply.index("def edit(buf):")
        execute_pos = apply.index("return self.execute_command")
        self.assertLess(branch_pos, edit_pos)
        self.assertLess(edit_pos, execute_pos)
        self.assertIn("if not changed:\n                return False", apply)
        self.assertIn(
            "command_transform_range(current, start, end, lambda _text: new)",
            apply,
        )

    def test_visible_entrypoint_preserves_existing_transform_pipeline(self):
        _source, methods = app_methods()
        method = methods["on_sentence_case"]
        self.assertEqual(
            method.strip(),
            'def on_sentence_case(self, *_):\n'
            '        return self.apply_text_transform(sentence_case, "Sentence Case")',
        )
        apply = methods["apply_text_transform"]
        self.assertIn("start, end = self.selected_or_all_range()", apply)
        self.assertIn(
            "return self.execute_command(command_name, edit, select_range=select)",
            apply,
        )

    def test_layer_dynamic_change_noop_and_existing_semantics(self):
        layer = CommandLayer(build_low_risk_registry())
        source = "È GIÀ QUI. POI ARRIVA L'AMICO!"
        changed = layer.dispatch(
            "writing.sentence-case",
            CommandContext(source="test", data={"text": source}),
        )
        self.assertTrue(changed.success)
        self.assertTrue(changed.changed)
        self.assertEqual(changed.value["text"], sentence_case(source))
        self.assertEqual(changed.value["text"], "È già qui. Poi arriva l'amico!")

        noop_text = "È già qui. Poi arriva l'amico!"
        noop = layer.dispatch(
            "writing.sentence-case",
            CommandContext(source="test", data={"text": noop_text}),
        )
        self.assertTrue(noop.success)
        self.assertFalse(noop.changed)
        self.assertEqual(noop.value["text"], noop_text)

    def test_layer_matches_existing_pure_semantics_across_edge_cases(self):
        layer = CommandLayer(build_low_risk_registry())
        cases = [
            "", "   ", "CIAO. MONDO", "ciao? sì! bene… ottimo",
            "UNO\nDUE", "UNO.\nDUE", "UNO.\n\nDUE",
            "È GIÀ QUI. POI ARRIVA L'AMICO!", "123 ABC. 456 DEF",
            "\nCIAO", '"CIAO." MONDO', "CIAO!\tMONDO", "CIAO… MONDO",
        ]
        for text in cases:
            with self.subTest(text=repr(text)):
                expected = sentence_case(text)
                result = layer.dispatch(
                    "writing.sentence-case",
                    CommandContext(source="test", data={"text": text}),
                )
                self.assertTrue(result.success)
                self.assertEqual(result.value["text"], expected)
                self.assertEqual(result.changed, expected != text)

    def test_algorithm_and_command_layer_remain_gtk_and_file_free(self):
        writing = (ROOT / "calamus" / "calamus_writing.py").read_text(encoding="utf-8")
        tree = ast.parse(writing)
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "sentence_case"
        )
        segment = ast.get_source_segment(writing, function)
        self.assertIn("text.lower()", segment)
        self.assertIn("re.sub", segment)
        self.assertIn("m.group(2).upper()", segment)
        for forbidden in ["Gtk", "Gdk", "open(", "write_text_file", "get_buffer"]:
            self.assertNotIn(forbidden, segment)

    def test_metadata_only_insert_datetime_stays_outside_dispatch_surface(self):
        source = BIN.read_text(encoding="utf-8")
        self.assertNotIn('"writing.insert-date-time"', source)


if __name__ == "__main__":
    unittest.main()
