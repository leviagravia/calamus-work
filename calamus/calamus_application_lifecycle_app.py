"""Narrow application-boundary wiring for the GTK-free lifecycle coordinator."""
from __future__ import annotations


def configure_application_lifecycle(
    lifecycle,
    *,
    pandoc_shutdown,
    shutdown_sources,
    navigator_shutdown,
    research_view_shutdown,
    research_coordinator_shutdown,
    document_overview_shutdown,
    typewriter_shutdown,
    history_shutdown,
    viewport_shutdown,
) -> None:
    callbacks = (
        pandoc_shutdown,
        shutdown_sources,
        navigator_shutdown,
        research_view_shutdown,
        research_coordinator_shutdown,
        document_overview_shutdown,
        typewriter_shutdown,
        history_shutdown,
        viewport_shutdown,
    )
    if not all(callable(callback) for callback in callbacks):
        raise TypeError("lifecycle shutdown capabilities must be callable")
    lifecycle.register_pre_destroy("pandoc-export", pandoc_shutdown)
    lifecycle.register_final("application-sources", shutdown_sources)
    lifecycle.register_final("navigator-panel", navigator_shutdown)
    lifecycle.register_final("research-panel-view", research_view_shutdown)
    lifecycle.register_final("research-coordinator", research_coordinator_shutdown)
    lifecycle.register_final("document-overview", document_overview_shutdown)
    lifecycle.register_final("typewriter", typewriter_shutdown)
    lifecycle.register_final("history", history_shutdown)
    lifecycle.register_final("viewport", viewport_shutdown)


def shutdown_application_sources(source_ids, remove_source, cancel_search_highlight) -> bool:
    """Cancel shell-owned GLib sources after the shell has cleared its slots."""
    if not callable(remove_source) or not callable(cancel_search_highlight):
        raise TypeError("source cancellation capabilities must be callable")
    for source in tuple(source_ids):
        if source is None:
            continue
        try:
            remove_source(source)
        except Exception:
            pass
    cancel_search_highlight(remove_source)
    return True
