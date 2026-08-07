from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from calamus_search_runtime import SearchApplicationRuntime, SearchRuntimePorts
from calamus_spellcheck_runtime import SpellcheckApplicationRuntime, SpellcheckRuntimePorts
from calamus_workspace_host_runtime import WorkspaceHostPorts, WorkspaceHostRuntime


class _Iter:
    def __init__(self, buffer, offset):
        self.buffer = buffer
        self.offset = offset


class _Buffer:
    def __init__(self, text):
        self.text = text

    def get_iter_at_offset(self, offset):
        return _Iter(self, offset)

    def get_bounds(self):
        return _Iter(self, 0), _Iter(self, len(self.text))

    def get_start_iter(self):
        return _Iter(self, 0)

    def delete(self, start, end):
        self.text = self.text[:start.offset] + self.text[end.offset:]

    def insert(self, iterator, text):
        off = iterator.offset
        self.text = self.text[:off] + text + self.text[off:]


class _BufferAdapter:
    def __init__(self, buffer):
        self.buffer = buffer

    def capture(self):
        return SimpleNamespace(text=self.buffer.text)


class _Transaction:
    def __init__(self, buffer):
        self.buffer = buffer
        self.calls = []

    def execute_command(self, label, edit_func, *, select_range=None):
        before = self.buffer.text
        edit_func(self.buffer)
        self.calls.append((label, select_range))
        return SimpleNamespace(changed=self.buffer.text != before)


class _SearchController:
    def __init__(self):
        self.query = SimpleNamespace(options=SimpleNamespace(wrap=True))
        self.configured = None
        self.current_replacement = None
        self.replaced_all = None
        self.committed = None

    def has_query(self): return True
    def repeat(self, *, backwards=False): return not backwards
    def matches(self, needle, **kwargs): return (needle, kwargs)
    def highlight(self, needle, **kwargs): return 2
    def find(self, needle, **kwargs): return kwargs.get("backwards", False) is False
    def configure(self, needle, **kwargs): self.configured = (needle, kwargs)
    def prepare_current_replacement(self, replacement):
        self.current_replacement = replacement
        return (1, 4, replacement, (1, 1 + len(replacement)))
    def commit_current_replacement(self, next_match): self.committed = next_match
    def prepare_replace_all(self, replacement):
        self.replaced_all = replacement
        return (replacement + " " + replacement, 2)
    def clear_current_match(self): self.committed = None


class W107SubsystemHostPortTests(unittest.TestCase):
    def test_search_runtime_owns_mutation_and_projection_without_app(self):
        buffer = _Buffer("xoldz")
        tx = _Transaction(buffer)
        projected = []
        controller = _SearchController()
        runtime = SearchApplicationRuntime(
            controller,
            tx,
            _BufferAdapter(buffer),
            SearchRuntimePorts(
                open_find_replace=lambda *args: args,
                open_find_all=lambda: (),
                show_info=lambda message: None,
                project_committed_change=projected.append,
            ),
        )
        self.assertTrue(runtime.replace_current_match("old", "NEW"))
        self.assertEqual(buffer.text, "xNEWz")
        self.assertEqual(tx.calls, [("Replace Selection", (1, 4))])
        self.assertEqual(projected, ["Replace Selection"])
        self.assertEqual(controller.committed, (1, 4))
        self.assertFalse(hasattr(runtime, "app"))

    def test_search_replace_all_is_one_editor_transaction(self):
        buffer = _Buffer("old old")
        tx = _Transaction(buffer)
        projected = []
        controller = _SearchController()
        runtime = SearchApplicationRuntime(
            controller,
            tx,
            _BufferAdapter(buffer),
            SearchRuntimePorts(lambda *args: None, lambda: None, lambda _m: None, projected.append),
        )
        self.assertEqual(runtime.replace_all_literal("old", "new"), 2)
        self.assertEqual(buffer.text, "new new")
        self.assertEqual([call[0] for call in tx.calls], ["Replace All"])
        self.assertEqual(projected, ["Replace All"])

    def test_spellcheck_runtime_is_widget_free_and_uses_transaction_port(self):
        buffer = _Buffer("bad word")
        tx = _Transaction(buffer)
        projected = []
        selected = []
        info = []
        runtime = SpellcheckApplicationRuntime(
            tx,
            _BufferAdapter(buffer),
            SpellcheckRuntimePorts(
                language_provider=lambda: "en_US",
                update_language=lambda _lang: True,
                spelling_dialog=lambda word, suggestions: (20, "good"),
                decode_response=lambda response: {20: "replace"}.get(response, "cancel"),
                show_info=info.append,
                show_error=lambda message: self.fail(message),
                clear_spell_tags=lambda: None,
                select_range=lambda start, end: selected.append((start, end)),
                update_title=lambda: None,
                project_committed_change=projected.append,
            ),
        )
        with patch("calamus_spellcheck_runtime.spell_hunspell_base_command", return_value=["hunspell"]), \
             patch("calamus_spellcheck_runtime.spell_hunspell_misspelled_words", return_value={"bad"}), \
             patch("calamus_spellcheck_runtime.spell_hunspell_suggestions", return_value=["good"]):
            runtime.on_check()
        self.assertEqual(buffer.text, "good word")
        self.assertEqual(selected, [(0, 3)])
        self.assertEqual(projected, ["Replace Selection"])
        self.assertIn("Replacements: 1", info[-1])
        self.assertFalse(hasattr(runtime, "text_view"))
        self.assertFalse(hasattr(runtime, "app"))

    def test_workspace_host_receives_narrow_state_direct_collaborators_and_ports(self):
        events = []
        ports = WorkspaceHostPorts(
            render_recent_workspaces=lambda paths: events.append(("rows", paths)),
            choose_root=lambda current: "/tmp/work",
            prompt_new_text_file=lambda destination: None,
            prompt_new_folder=lambda destination: None,
            prompt_rename_item=lambda name, is_dir: None,
            confirm_trash=lambda name, is_dir, active: True,
            show_error=lambda message: events.append(("error", message)),
            document_text=lambda: "text",
            research_context_changed=lambda: events.append(("research",)),
            update_title=lambda: events.append(("title",)),
            refresh_overview=lambda: events.append(("overview",)),
            refresh_ui_state=lambda: events.append(("ui",)),
        )
        store = SimpleNamespace(visible=lambda: ["/a"], canonical=lambda: ["/a"], save=lambda rows: True)
        state = SimpleNamespace(record_last_file=lambda path: True, record_workspace_visible=lambda value: True)
        session = SimpleNamespace(file_path=None)
        application_runtime = SimpleNamespace(root="/work")
        mutation_controller = SimpleNamespace()
        mutation_runtime = SimpleNamespace()
        panel_view = SimpleNamespace()
        panel_runtime = SimpleNamespace()
        runtime = WorkspaceHostRuntime(
            recent_workspaces=store,
            recent_files=store,
            favourites=store,
            application_state=state,
            document_session=session,
            application_runtime=application_runtime,
            mutation_controller=mutation_controller,
            mutation_runtime=mutation_runtime,
            panel_view=panel_view,
            panel_runtime=panel_runtime,
            ports=ports,
        )
        self.assertEqual(runtime.populate_recent_workspaces_menu(), ("/a",))
        self.assertEqual(events, [("rows", ("/a",))])
        self.assertEqual(runtime.root, "/work")
        self.assertIs(runtime._application_runtime, application_runtime)
        self.assertIs(runtime._mutation_controller, mutation_controller)
        self.assertIs(runtime._mutation_runtime, mutation_runtime)
        self.assertIs(runtime._panel_view, panel_view)
        self.assertIs(runtime._panel_runtime, panel_runtime)
        self.assertFalse(hasattr(runtime, "components"))
        self.assertFalse(hasattr(runtime, "_components"))
        self.assertFalse(hasattr(runtime, "_parent"))
        self.assertFalse(hasattr(runtime, "app"))

    def test_port_records_reject_non_callable_capabilities(self):
        with self.assertRaises(TypeError):
            SearchRuntimePorts(None, lambda: None, lambda _m: None, lambda _m: None)
        with self.assertRaises(TypeError):
            WorkspaceHostPorts(
                render_recent_workspaces=None,
                choose_root=lambda _r: None,
                prompt_new_text_file=lambda _d: None,
                prompt_new_folder=lambda _d: None,
                prompt_rename_item=lambda _n, _d: None,
                confirm_trash=lambda *_a: True,
                show_error=lambda _m: None,
                document_text=lambda: "",
                research_context_changed=lambda: None,
                update_title=lambda: None,
                refresh_overview=lambda: None,
                refresh_ui_state=lambda: None,
            )


if __name__ == "__main__":
    unittest.main()
