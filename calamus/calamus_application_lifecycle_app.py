"""Application-boundary wiring for the GTK-free lifecycle coordinator."""
from __future__ import annotations


def configure_application_lifecycle(app) -> None:
    lifecycle = app.application_lifecycle
    lifecycle.register_pre_destroy("pandoc-export", app.pandoc_export_runtime.shutdown)
    lifecycle.register_final(
        "application-sources", app.shutdown_application_sources
    )
    lifecycle.register_final("navigator-panel", app.navigator_panel_runtime.shutdown)
    lifecycle.register_final("research-panel-view", app.research_panel_view.shutdown)
    lifecycle.register_final("research-coordinator", app.research_coordinator.shutdown)
    lifecycle.register_final("document-overview", app.document_overview_runtime.shutdown)
    lifecycle.register_final("typewriter", app.typewriter_runtime.shutdown)
    lifecycle.register_final("history", app.history_runtime.shutdown)
    lifecycle.register_final("viewport", app.viewport_runtime.shutdown)


def shutdown_application_sources(app, remove_source) -> bool:
    if not callable(remove_source):
        raise TypeError("remove_source must be callable")
    for attribute in ("spell_source", "word_count_source", "_wrap_reflow_source"):
        source = getattr(app, attribute, None)
        setattr(app, attribute, None)
        if source is None:
            continue
        try:
            remove_source(source)
        except Exception:
            pass
    search_controller = getattr(app, "search_controller", None)
    if search_controller is not None:
        search_controller.cancel_pending_highlight(remove_source)
    return True
