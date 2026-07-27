"""Thin GTK runtime for the W90 external Pandoc/citeproc workflow.

The runtime owns orchestration only.  Dialogs, background execution and result
presentation are injected semantic boundaries.  Production uses the GTK
adapters below; tests can replace those boundaries without replacing the App,
controller, reference stores or real Pandoc process.
"""
from __future__ import annotations

from dataclasses import dataclass
import threading
from typing import Callable

from calamus_modal_dialog import ModalSession
from calamus_pandoc import PandocExportRequest
from calamus_pandoc_controller import PandocExportController


def _default_options(parent, names):
    from calamus_pandoc_dialogs import run_pandoc_options_dialog
    return run_pandoc_options_dialog(parent, names)


def _default_destination(parent, document_path, product, format_id):
    from calamus_pandoc_dialogs import run_pandoc_destination_dialog
    return run_pandoc_destination_dialog(parent, document_path, product, format_id)


def _default_preview(parent, plan, preview):
    from calamus_pandoc_dialogs import run_pandoc_preview_dialog
    return run_pandoc_preview_dialog(parent, plan, preview)


def _default_progress(parent, title):
    from calamus_pandoc_dialogs import build_pandoc_progress_dialog
    return build_pandoc_progress_dialog(parent, title)


def _default_error(parent, message):
    from calamus_pandoc_dialogs import show_pandoc_error
    show_pandoc_error(parent, message)


def _default_result(parent, result):
    from calamus_pandoc_dialogs import show_pandoc_result
    show_pandoc_result(parent, result)


@dataclass(frozen=True)
class PandocWorkflowOutcome:
    """Stable terminal state for one complete export request."""

    status: str
    stage: str
    message: str = ""
    path: str = ""

    @property
    def succeeded(self) -> bool:
        return self.status == "exported"


class PandocExportRuntime:
    def __init__(
        self,
        parent,
        controller: PandocExportController,
        *,
        document_path_provider: Callable[[], str | None],
        reference_set_names_provider: Callable[[], tuple[str, ...]],
        options_chooser=_default_options,
        destination_chooser=_default_destination,
        preview_presenter=_default_preview,
        progress_builder=_default_progress,
        show_error=_default_error,
        show_result=_default_result,
        operation_executor=None,
    ) -> None:
        if not isinstance(controller, PandocExportController):
            raise TypeError("controller must be PandocExportController")
        dependencies = (
            document_path_provider,
            reference_set_names_provider,
            options_chooser,
            destination_chooser,
            preview_presenter,
            progress_builder,
            show_error,
            show_result,
        )
        if not all(callable(value) for value in dependencies):
            raise TypeError("Pandoc runtime dependencies must be callable")
        if operation_executor is not None and not callable(operation_executor):
            raise TypeError("operation_executor must be callable or None")
        self._parent = parent
        self._controller = controller
        self._document_path_provider = document_path_provider
        self._reference_set_names_provider = reference_set_names_provider
        self._options_chooser = options_chooser
        self._destination_chooser = destination_chooser
        self._preview_presenter = preview_presenter
        self._progress_builder = progress_builder
        self._show_error = show_error
        self._show_result = show_result
        self._operation_executor = operation_executor
        self._state_lock = threading.RLock()
        self._thread: threading.Thread | None = None
        self._last_outcome = PandocWorkflowOutcome("idle", "idle")

    @property
    def busy(self) -> bool:
        with self._state_lock:
            return self._thread is not None and self._thread.is_alive()

    @property
    def last_outcome(self) -> PandocWorkflowOutcome:
        with self._state_lock:
            return self._last_outcome

    def _record(self, status: str, stage: str, message: str = "", path: str = "") -> None:
        with self._state_lock:
            self._last_outcome = PandocWorkflowOutcome(status, stage, message, path)

    def _fail(self, stage: str, message: str) -> bool:
        self._record("error", stage, message)
        self._show_error(self._parent, message)
        return False

    def export(self) -> bool:
        if self.busy:
            return self._fail("busy", "Another Pandoc export is already active.")
        self._record("running", "options")
        try:
            set_names = tuple(self._reference_set_names_provider())
        except Exception as error:
            return self._fail("reference-sets", str(error))
        try:
            options = self._options_chooser(self._parent, set_names)
        except Exception as error:
            return self._fail("options", str(error))
        if options is None:
            self._record("cancelled", "options")
            return False
        try:
            product, scope, format_id, set_name, csl_path = options
        except (TypeError, ValueError) as error:
            return self._fail("options", str(error))
        document_path = self._document_path_provider()
        try:
            destination = self._destination_chooser(
                self._parent,
                document_path,
                product,
                format_id,
            )
        except Exception as error:
            return self._fail("destination", str(error))
        if not destination:
            self._record("cancelled", "destination")
            return False
        try:
            request = PandocExportRequest(
                product,
                scope,
                format_id,
                destination,
                set_name,
                csl_path,
            )
        except (TypeError, ValueError) as error:
            return self._fail("request", str(error))

        self._record("running", "prepare")
        try:
            plan = self._execute_operation(
                "Checking Pandoc and freezing the export plan…",
                lambda: self._controller.prepare_export(request),
            )
        except Exception as error:
            return self._fail("prepare", str(error))
        if plan is None:
            if self.last_outcome.status != "error":
                self._record("cancelled", "prepare")
            return False

        self._record("running", "preview")
        try:
            preview = self._execute_operation(
                "Generating semantic citeproc preview…",
                lambda: self._controller.build_preview(plan),
            )
        except Exception as error:
            return self._fail("preview", str(error))
        if preview is None:
            if self.last_outcome.status != "error":
                self._record("cancelled", "preview")
            return False
        if not preview.succeeded:
            return self._fail("preview", preview.message)
        try:
            accepted = self._preview_presenter(self._parent, plan, preview)
        except Exception as error:
            return self._fail("preview-confirmation", str(error))
        if not accepted:
            self._record("cancelled", "preview-confirmation")
            return False

        self._record("running", "export")
        try:
            result = self._execute_operation(
                "Exporting with Pandoc/citeproc…",
                lambda: self._controller.apply_export(plan),
            )
        except Exception as error:
            return self._fail("export", str(error))
        if result is None:
            if self.last_outcome.status != "error":
                self._record("cancelled", "export")
            return False
        self._show_result(self._parent, result)
        if result.succeeded:
            self._record("exported", "result", result.message, result.path)
            return True
        self._record(result.status or "error", "result", result.message, result.path)
        return False

    def shutdown(self, *, join_timeout: float = 8.0) -> bool:
        self._controller.cancel_active()
        with self._state_lock:
            thread = self._thread
        if thread is not None and thread.is_alive():
            thread.join(max(0.1, float(join_timeout)))
        worker_stopped = not (thread is not None and thread.is_alive())
        return worker_stopped and self._controller.active_pid is None

    def _execute_operation(self, title: str, operation):
        executor = self._operation_executor
        if executor is not None:
            return executor(title, operation)
        return self._background(title, operation)

    def _background(self, title: str, operation):
        import gi
        gi.require_version("GLib", "2.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import GLib, Gtk

        widgets = self._progress_builder(self._parent, title)
        holder: dict[str, object] = {}
        source_state = {"active": False}
        session = ModalSession(widgets.dialog)

        def worker():
            try:
                holder["result"] = operation()
            except Exception as error:
                holder["error"] = error

        thread = threading.Thread(target=worker, name="calamus-pandoc-worker", daemon=False)
        with self._state_lock:
            if self._thread is not None and self._thread.is_alive():
                session.close()
                self._fail("busy", "Another Pandoc export is already active.")
                return None
            self._thread = thread
        thread.start()

        def poll_worker():
            if thread.is_alive():
                return True
            source_state["active"] = False
            widgets.dialog.response(Gtk.ResponseType.OK)
            return False

        def remove_poll_source(source_id: int):
            if source_state["active"]:
                GLib.source_remove(source_id)
                source_state["active"] = False

        source_id = GLib.timeout_add(50, poll_worker)
        source_state["active"] = True
        session.register_source(source_id, remove_poll_source)
        try:
            response = session.run()
            if response != Gtk.ResponseType.OK:
                self._controller.cancel_active()
            thread.join(10.0)
            if thread.is_alive():
                self._controller.cancel_active()
                thread.join(3.0)
            if thread.is_alive():
                self._fail(
                    "worker-shutdown",
                    "Pandoc worker did not terminate cleanly; no final output was accepted.",
                )
                return None
            if response != Gtk.ResponseType.OK:
                return None
            error = holder.get("error")
            if error is not None:
                self._fail("operation", str(error))
                return None
            return holder.get("result")
        finally:
            try:
                session.close()
            finally:
                with self._state_lock:
                    if self._thread is thread:
                        self._thread = None
