"""GTK-free application ownership and shutdown coordination.

W99 centralizes the lifecycle that was previously distributed across the
launcher.  The coordinator owns only callback ordering and reports; concrete
GTK/GLib objects remain behind injected callbacks at the application boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


LifecycleCallback = Callable[[], Any]


@dataclass(frozen=True)
class LifecycleFailure:
    phase: str
    owner: str
    detail: str


@dataclass(frozen=True)
class LifecycleReport:
    phase: str
    attempted: tuple[str, ...]
    completed: tuple[str, ...]
    failures: tuple[LifecycleFailure, ...]

    @property
    def ok(self) -> bool:
        return not self.failures


@dataclass(frozen=True)
class _LifecycleEntry:
    name: str
    callback: LifecycleCallback


class ApplicationLifecycleCoordinator:
    """Own deterministic pre-destroy and final-shutdown callbacks.

    Pre-destroy callbacks may veto an interactive close by returning exactly
    ``False`` or by raising. Successful pre-destroy callbacks are not repeated
    during final shutdown. Final shutdown is fail-complete: every registered
    callback receives one attempt even when an earlier owner fails.
    """

    def __init__(self) -> None:
        self._pre_destroy: list[_LifecycleEntry] = []
        self._final: list[_LifecycleEntry] = []
        self._names: set[str] = set()
        self._pre_destroy_completed: set[str] = set()
        self._shutdown_report: LifecycleReport | None = None

    @property
    def registered_pre_destroy(self) -> tuple[str, ...]:
        return tuple(entry.name for entry in self._pre_destroy)

    @property
    def registered_final(self) -> tuple[str, ...]:
        return tuple(entry.name for entry in self._final)

    @property
    def is_shutdown(self) -> bool:
        return self._shutdown_report is not None

    @property
    def shutdown_report(self) -> LifecycleReport | None:
        return self._shutdown_report

    def register_pre_destroy(self, name: str, callback: LifecycleCallback) -> None:
        self._register(self._pre_destroy, name, callback)

    def register_final(self, name: str, callback: LifecycleCallback) -> None:
        self._register(self._final, name, callback)

    def preflight(self) -> LifecycleReport:
        """Run close-blocking callbacks, stopping at the first failure."""
        if self.is_shutdown:
            return LifecycleReport("pre-destroy", (), (), ())
        attempted: list[str] = []
        completed: list[str] = []
        failures: list[LifecycleFailure] = []
        for entry in self._pre_destroy:
            if entry.name in self._pre_destroy_completed:
                continue
            attempted.append(entry.name)
            failure = self._invoke("pre-destroy", entry)
            if failure is not None:
                failures.append(failure)
                break
            self._pre_destroy_completed.add(entry.name)
            completed.append(entry.name)
        return LifecycleReport(
            "pre-destroy", tuple(attempted), tuple(completed), tuple(failures)
        )

    def shutdown(self) -> LifecycleReport:
        """Shut every remaining owner down once and aggregate all failures."""
        if self._shutdown_report is not None:
            return self._shutdown_report
        attempted: list[str] = []
        completed: list[str] = []
        failures: list[LifecycleFailure] = []

        for entry in self._pre_destroy:
            if entry.name in self._pre_destroy_completed:
                continue
            attempted.append(entry.name)
            failure = self._invoke("final-pre-destroy", entry)
            if failure is None:
                self._pre_destroy_completed.add(entry.name)
                completed.append(entry.name)
            else:
                failures.append(failure)

        for entry in self._final:
            attempted.append(entry.name)
            failure = self._invoke("final", entry)
            if failure is None:
                completed.append(entry.name)
            else:
                failures.append(failure)

        self._shutdown_report = LifecycleReport(
            "final", tuple(attempted), tuple(completed), tuple(failures)
        )
        return self._shutdown_report

    def _register(
        self,
        target: list[_LifecycleEntry],
        name: str,
        callback: LifecycleCallback,
    ) -> None:
        if self.is_shutdown:
            raise RuntimeError("application lifecycle is already shut down")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("lifecycle owner name must be non-empty")
        normalized = name.strip()
        if normalized in self._names:
            raise ValueError(f"lifecycle owner already registered: {normalized}")
        if not callable(callback):
            raise TypeError("lifecycle callback must be callable")
        self._names.add(normalized)
        target.append(_LifecycleEntry(normalized, callback))

    @staticmethod
    def _invoke(phase: str, entry: _LifecycleEntry) -> LifecycleFailure | None:
        try:
            result = entry.callback()
        except Exception as exc:  # Lifecycle must preserve later owners.
            return LifecycleFailure(phase, entry.name, f"{type(exc).__name__}: {exc}")
        if result is False:
            return LifecycleFailure(phase, entry.name, "callback returned False")
        return None
