"""GTK-free coordination contract for the seven built-in Research clients.

W98 deliberately adds one small, fixed coordinator rather than a plugin system
or generic event bus.  It owns typed invalidation, hidden-client dirty state,
coalesced document-content delivery, and idempotent Research shutdown.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Hashable, Iterable


DOCUMENT_CONTENT_QUIET_MS = 150
BUILTIN_RESEARCH_CLIENT_IDS = (
    "clip-collection",
    "scratchpad",
    "references",
    "tags",
    "reference-sets",
    "source-notes",
    "authoring-bridge",
)


class ResearchInvalidationReason(str, Enum):
    DOCUMENT_IDENTITY = "document-identity"
    DOCUMENT_CONTENT = "document-content"
    REFERENCES = "references"
    SOURCE_NOTES = "source-notes"
    SCRATCHPAD = "scratchpad"
    REFERENCE_SETS = "reference-sets"
    CLIPS = "clips"


InvalidationSet = frozenset[ResearchInvalidationReason]


@dataclass(frozen=True)
class ResearchClientSpec:
    """One fixed built-in Research client and its explicit dependencies."""

    client_id: str
    title: str
    widget: Any
    activate: Callable[[], Any]
    dependencies: InvalidationSet
    invalidate: Callable[[InvalidationSet], Any]
    shutdown: Callable[[], Any]

    def __post_init__(self) -> None:
        if self.client_id not in BUILTIN_RESEARCH_CLIENT_IDS:
            raise ValueError(f"unknown built-in Research client: {self.client_id}")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("Research client title must be non-empty")
        if self.widget is None:
            raise TypeError("Research client widget is required")
        if any(not callable(callback) for callback in (
            self.activate, self.invalidate, self.shutdown
        )):
            raise TypeError("Research client callbacks must be callable")
        if not isinstance(self.dependencies, frozenset):
            raise TypeError("Research client dependencies must be a frozenset")
        if any(not isinstance(reason, ResearchInvalidationReason)
               for reason in self.dependencies):
            raise TypeError("Research client dependencies contain an invalid reason")


class ResearchPanelCoordinator:
    """Coordinate invalidation and lifecycle for the fixed Research subsystem."""

    def __init__(
        self,
        *,
        active_client_provider: Callable[[], str | None],
        schedule: Callable[[int, Callable[[], bool]], Hashable],
        cancel: Callable[[Hashable], Any],
        quiet_period_ms: int = DOCUMENT_CONTENT_QUIET_MS,
    ) -> None:
        if any(not callable(callback) for callback in (
            active_client_provider, schedule, cancel
        )):
            raise TypeError("Research coordinator callbacks must be callable")
        if not isinstance(quiet_period_ms, int) or isinstance(quiet_period_ms, bool):
            raise TypeError("quiet_period_ms must be an integer")
        if quiet_period_ms < 1 or quiet_period_ms > 2000:
            raise ValueError("quiet_period_ms must be between 1 and 2000")
        self._active_client_provider = active_client_provider
        self._schedule = schedule
        self._cancel = cancel
        self._quiet_period_ms = quiet_period_ms
        self._specs: dict[str, ResearchClientSpec] = {}
        self._dirty: dict[str, set[ResearchInvalidationReason]] = {}
        self._content_source: Hashable | None = None
        self._generation = 0
        self._shutdown = False
        self._shutdown_clients: set[str] = set()
        self._delivery_count = 0

    @property
    def registered_ids(self) -> tuple[str, ...]:
        return tuple(self._specs)

    @property
    def pending_content(self) -> bool:
        return self._content_source is not None

    @property
    def delivery_count(self) -> int:
        return self._delivery_count

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown

    def dirty_reasons(self, client_id: str) -> InvalidationSet:
        return frozenset(self._dirty.get(client_id, ()))

    def register(self, spec: ResearchClientSpec) -> None:
        if self._shutdown:
            raise RuntimeError("Research coordinator is shut down")
        if not isinstance(spec, ResearchClientSpec):
            raise TypeError("spec must be ResearchClientSpec")
        if spec.client_id in self._specs:
            raise ValueError(f"Research client already registered: {spec.client_id}")
        self._specs[spec.client_id] = spec
        self._dirty[spec.client_id] = set()

    def assert_complete(self) -> None:
        actual = tuple(self._specs)
        if actual != BUILTIN_RESEARCH_CLIENT_IDS:
            raise RuntimeError(
                "Research client registration is incomplete or out of order: "
                f"{actual!r}"
            )

    def activate(self, client_id: str) -> Any:
        if self._shutdown:
            return False
        spec = self._require_spec(client_id)
        # Every existing runtime activation already performs one refresh.  A
        # dirty hidden client therefore refreshes exactly once here, not once
        # via invalidate plus a second time via activate.
        self._dirty[client_id].clear()
        return spec.activate()

    def publish(
        self,
        reasons: ResearchInvalidationReason | Iterable[ResearchInvalidationReason],
    ) -> None:
        if self._shutdown:
            return
        normalized = self._normalize(reasons)
        if not normalized:
            return
        if ResearchInvalidationReason.DOCUMENT_IDENTITY in normalized:
            self.cancel_pending_content()
        immediate = normalized - {ResearchInvalidationReason.DOCUMENT_CONTENT}
        if immediate:
            self._deliver(frozenset(immediate))
        if ResearchInvalidationReason.DOCUMENT_CONTENT in normalized:
            self._schedule_document_content()

    def cancel_pending_content(self) -> None:
        self._generation += 1
        source = self._content_source
        self._content_source = None
        if source is not None:
            try:
                self._cancel(source)
            except Exception:
                pass

    def shutdown(self) -> bool:
        if self._shutdown:
            return True
        self._shutdown = True
        self.cancel_pending_content()
        for client_id, spec in self._specs.items():
            if client_id in self._shutdown_clients:
                continue
            try:
                spec.shutdown()
            finally:
                self._shutdown_clients.add(client_id)
        self._dirty.clear()
        return True

    def _schedule_document_content(self) -> None:
        self._generation += 1
        generation = self._generation
        source = self._content_source
        self._content_source = None
        if source is not None:
            try:
                self._cancel(source)
            except Exception:
                pass

        def deliver() -> bool:
            if self._shutdown or generation != self._generation:
                return False
            self._content_source = None
            self._deliver(frozenset({ResearchInvalidationReason.DOCUMENT_CONTENT}))
            return False

        self._content_source = self._schedule(self._quiet_period_ms, deliver)

    def _deliver(self, reasons: InvalidationSet) -> None:
        if self._shutdown or not reasons:
            return
        active = self._active_client_provider()
        for client_id, spec in self._specs.items():
            relevant = reasons.intersection(spec.dependencies)
            if not relevant:
                continue
            if client_id == active:
                spec.invalidate(frozenset(relevant))
                self._dirty[client_id].difference_update(relevant)
                self._delivery_count += 1
            else:
                self._dirty[client_id].update(relevant)

    def _require_spec(self, client_id: str) -> ResearchClientSpec:
        if client_id not in self._specs:
            raise KeyError(client_id)
        return self._specs[client_id]

    @staticmethod
    def _normalize(
        reasons: ResearchInvalidationReason | Iterable[ResearchInvalidationReason],
    ) -> InvalidationSet:
        if isinstance(reasons, ResearchInvalidationReason):
            return frozenset({reasons})
        try:
            normalized = frozenset(reasons)
        except TypeError as error:
            raise TypeError("reasons must be a Research invalidation reason or iterable") from error
        if any(not isinstance(reason, ResearchInvalidationReason) for reason in normalized):
            raise TypeError("invalid Research invalidation reason")
        return normalized
