from __future__ import annotations

import ast
from pathlib import Path
import unittest

from calamus_application_lifecycle import ApplicationLifecycleCoordinator
from calamus_research_coordination import (
    BUILTIN_RESEARCH_CLIENT_IDS,
    ResearchClientSpec,
    ResearchPanelCoordinator,
)


ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "calamus"


class ApplicationLifecycleCoordinatorTests(unittest.TestCase):
    def test_registration_is_named_ordered_and_unique(self):
        lifecycle = ApplicationLifecycleCoordinator()
        lifecycle.register_pre_destroy("worker", lambda: True)
        lifecycle.register_final("panel", lambda: True)
        self.assertEqual(lifecycle.registered_pre_destroy, ("worker",))
        self.assertEqual(lifecycle.registered_final, ("panel",))
        with self.assertRaisesRegex(ValueError, "already registered"):
            lifecycle.register_final("worker", lambda: True)
        with self.assertRaises(TypeError):
            lifecycle.register_final("invalid", object())

    def test_successful_preflight_is_not_repeated_during_final_shutdown(self):
        calls = []
        lifecycle = ApplicationLifecycleCoordinator()
        lifecycle.register_pre_destroy("worker", lambda: calls.append("worker") or True)
        lifecycle.register_final("panel", lambda: calls.append("panel") or True)
        self.assertTrue(lifecycle.preflight().ok)
        report = lifecycle.shutdown()
        self.assertTrue(report.ok)
        self.assertEqual(calls, ["worker", "panel"])
        self.assertEqual(report.attempted, ("panel",))
        self.assertIs(lifecycle.shutdown(), report)
        self.assertEqual(calls, ["worker", "panel"])

    def test_preflight_failure_blocks_but_can_be_retried(self):
        attempts = []
        lifecycle = ApplicationLifecycleCoordinator()

        def worker():
            attempts.append(len(attempts) + 1)
            return len(attempts) > 1

        lifecycle.register_pre_destroy("worker", worker)
        first = lifecycle.preflight()
        self.assertFalse(first.ok)
        self.assertEqual(first.failures[0].owner, "worker")
        self.assertTrue(lifecycle.preflight().ok)
        self.assertEqual(attempts, [1, 2])

    def test_final_shutdown_continues_and_aggregates_every_failure(self):
        calls = []
        lifecycle = ApplicationLifecycleCoordinator()
        lifecycle.register_pre_destroy(
            "worker", lambda: (_ for _ in ()).throw(RuntimeError("busy"))
        )
        lifecycle.register_final("first", lambda: calls.append("first") or False)
        lifecycle.register_final(
            "second", lambda: (_ for _ in ()).throw(ValueError("broken"))
        )
        lifecycle.register_final("third", lambda: calls.append("third") or True)
        report = lifecycle.shutdown()
        self.assertFalse(report.ok)
        self.assertEqual(report.attempted, ("worker", "first", "second", "third"))
        self.assertEqual(calls, ["first", "third"])
        self.assertEqual(
            tuple(failure.owner for failure in report.failures),
            ("worker", "first", "second"),
        )
        self.assertEqual(report.completed, ("third",))

    def test_registration_after_shutdown_is_rejected(self):
        lifecycle = ApplicationLifecycleCoordinator()
        lifecycle.shutdown()
        with self.assertRaisesRegex(RuntimeError, "already shut down"):
            lifecycle.register_final("late", lambda: True)


class W99ResearchShutdownTests(unittest.TestCase):
    def test_research_shutdown_is_failure_complete_and_idempotent(self):
        calls = []
        coordinator = ResearchPanelCoordinator(
            active_client_provider=lambda: None,
            schedule=lambda _delay, _callback: 1,
            cancel=lambda _source: True,
        )

        def shutdown_for(client_id):
            def shutdown():
                calls.append(client_id)
                if client_id == "scratchpad":
                    raise RuntimeError("scratchpad close failed")
                if client_id == "tags":
                    return False
                return True
            return shutdown

        for client_id in BUILTIN_RESEARCH_CLIENT_IDS:
            coordinator.register(
                ResearchClientSpec(
                    client_id=client_id,
                    title=client_id,
                    widget=object(),
                    activate=lambda: True,
                    dependencies=frozenset(),
                    invalidate=lambda _reasons: True,
                    shutdown=shutdown_for(client_id),
                )
            )
        coordinator.assert_complete()

        self.assertFalse(coordinator.shutdown())
        self.assertEqual(calls, list(BUILTIN_RESEARCH_CLIENT_IDS))
        self.assertEqual(
            coordinator.shutdown_failures,
            (
                ("scratchpad", "RuntimeError: scratchpad close failed"),
                ("tags", "callback returned False"),
            ),
        )
        self.assertFalse(coordinator.shutdown())
        self.assertEqual(calls, list(BUILTIN_RESEARCH_CLIENT_IDS))


class W99ApplicationLifecycleWiringTests(unittest.TestCase):
    def test_launcher_registers_the_complete_fixed_owner_inventory(self):
        text = (
            ROOT / "calamus" / "calamus_application_lifecycle_app.py"
        ).read_text(encoding="utf-8")
        expected = (
            'register_pre_destroy("pandoc-export"',
            '"application-sources", app.shutdown_application_sources',
            'register_final("navigator-panel"',
            'register_final("research-panel-view"',
            'register_final("research-coordinator"',
            'register_final("document-overview"',
            'register_final("typewriter"',
            'register_final("history"',
            'register_final("viewport"',
        )
        for token in expected:
            self.assertIn(token, text)
        self.assertEqual(text.count("register_pre_destroy("), 1)
        self.assertEqual(text.count("register_final("), 8)

    def test_close_gateway_uses_only_central_lifecycle_authority(self):
        source = LAUNCHER.read_text(encoding="utf-8")
        tree = ast.parse(source)
        methods = {
            node.name: ast.get_source_segment(source, node) or ""
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name in {"request_application_close", "on_destroy"}
        }
        request = methods["request_application_close"]
        destroy = methods["on_destroy"]
        self.assertIn("self.application_lifecycle.preflight()", request)
        self.assertNotIn("pandoc_export_runtime.shutdown", request)
        self.assertNotIn("research_coordinator.shutdown", request)
        self.assertIn("self.application_lifecycle.shutdown()", destroy)
        for legacy in (
            "research_coordinator.shutdown",
            "document_overview_runtime.shutdown",
            "typewriter_runtime.shutdown",
            "history_runtime.shutdown",
            "viewport_runtime.shutdown",
        ):
            self.assertNotIn(legacy, destroy)

    def test_all_launcher_glib_sources_have_one_shutdown_gateway(self):
        launcher = LAUNCHER.read_text(encoding="utf-8")
        boundary = (
            ROOT / "calamus" / "calamus_application_lifecycle_app.py"
        ).read_text(encoding="utf-8")
        self.assertIn("self._wrap_reflow_source = GLib.idle_add", launcher)
        self.assertIn("self.word_count_source = GLib.timeout_add", launcher)
        self.assertIn("search_controller.cancel_pending_highlight(remove_source)", boundary)
        self.assertIn(
            '("spell_source", "word_count_source", "_wrap_reflow_source")',
            boundary,
        )


if __name__ == "__main__":
    unittest.main()
