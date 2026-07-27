"""Tracked shell-free Pandoc process adapter for Calamus W90."""
from __future__ import annotations

from dataclasses import dataclass
import os
import re
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from typing import Iterable

_MINIMUM_VERSION = (2, 11, 0)
_VERSION_RE = re.compile(r"^pandoc\s+(?P<version>\d+(?:\.\d+)+)", re.IGNORECASE)
_STDERR_LIMIT = 64 * 1024
_STDOUT_LIMIT = 64 * 1024


@dataclass(frozen=True)
class PandocIdentity:
    path: str
    version: str
    version_parts: tuple[int, ...]


@dataclass(frozen=True)
class PandocProcessResult:
    status: str
    argv: tuple[str, ...]
    returncode: int | None
    stdout: str
    stderr: str
    elapsed_seconds: float

    @property
    def succeeded(self) -> bool:
        return self.status == "success"


class PandocProcessRunner:
    """Own exactly one active Pandoc child and its cancellation boundary."""

    def __init__(self, *, executable_name: str = "pandoc") -> None:
        if not isinstance(executable_name, str) or not executable_name.strip():
            raise ValueError("executable_name is required")
        self._executable_name = executable_name.strip()
        self._lock = threading.RLock()
        self._active: subprocess.Popen | None = None
        self._cancel_requested = threading.Event()

    @property
    def active_pid(self) -> int | None:
        with self._lock:
            process = self._active
            return process.pid if process is not None and process.poll() is None else None

    def locate(self) -> str:
        found = shutil.which(self._executable_name)
        if not found:
            raise ValueError(
                "Pandoc is not installed or is not available on PATH. "
                "Install Pandoc and try again."
            )
        path = os.path.realpath(os.path.abspath(found))
        if not os.path.isfile(path) or not os.access(path, os.X_OK):
            raise ValueError("The detected Pandoc executable is not a runnable regular file.")
        return path

    def detect(self, *, timeout_seconds: float = 5.0) -> PandocIdentity:
        path = self.locate()
        result = self.run((path, "--version"), timeout_seconds=timeout_seconds)
        if not result.succeeded:
            detail = result.stderr.strip() or result.stdout.strip() or result.status
            raise ValueError(f"Pandoc could not be started: {detail}")
        first_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
        match = _VERSION_RE.match(first_line)
        if not match:
            raise ValueError("Pandoc returned an unrecognized version string.")
        version = match.group("version")
        parts = tuple(int(item) for item in version.split("."))
        padded = parts + (0,) * max(0, len(_MINIMUM_VERSION) - len(parts))
        if padded[: len(_MINIMUM_VERSION)] < _MINIMUM_VERSION:
            required = ".".join(str(item) for item in _MINIMUM_VERSION)
            raise ValueError(f"Pandoc {required} or newer is required; detected {version}.")
        return PandocIdentity(path, version, parts)

    def run(
        self,
        argv: Iterable[str],
        *,
        cwd: str | None = None,
        timeout_seconds: float = 120.0,
    ) -> PandocProcessResult:
        args = tuple(argv)
        if not args or any(not isinstance(item, str) or not item for item in args):
            raise ValueError("Pandoc argv must contain non-empty strings.")
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        executable = os.path.realpath(os.path.abspath(args[0]))
        if executable != args[0]:
            args = (executable, *args[1:])
        if not os.path.isfile(executable) or not os.access(executable, os.X_OK):
            raise ValueError("Pandoc executable is not a runnable regular file.")
        working_directory = None
        if cwd is not None:
            working_directory = os.path.abspath(cwd)
            if not os.path.isdir(working_directory):
                raise ValueError("Pandoc working directory is unavailable.")

        with self._lock:
            if self._active is not None and self._active.poll() is None:
                raise RuntimeError("Another Pandoc process is already active.")
            self._cancel_requested.clear()

        creationflags = 0
        popen_kwargs: dict[str, object] = {}
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        else:
            popen_kwargs["start_new_session"] = True

        started = time.monotonic()
        status = "error"
        returncode: int | None = None
        process: subprocess.Popen | None = None
        with tempfile.TemporaryFile(prefix="calamus-pandoc-stdout-") as stdout_file, \
                tempfile.TemporaryFile(prefix="calamus-pandoc-stderr-") as stderr_file:
            try:
                process = subprocess.Popen(
                    args,
                    cwd=working_directory,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    shell=False,
                    creationflags=creationflags,
                    **popen_kwargs,
                )
                with self._lock:
                    if self._active is not None and self._active.poll() is None:
                        self._terminate(process)
                        raise RuntimeError("Another Pandoc process is already active.")
                    self._active = process

                while True:
                    if self._cancel_requested.is_set():
                        if not self._terminate(process):
                            raise RuntimeError("Pandoc process did not terminate after cancellation.")
                        returncode = process.returncode
                        status = "cancelled"
                        break
                    elapsed = time.monotonic() - started
                    if elapsed >= float(timeout_seconds):
                        if not self._terminate(process):
                            raise RuntimeError("Pandoc process did not terminate after timeout.")
                        returncode = process.returncode
                        status = "timeout"
                        break
                    try:
                        returncode = process.wait(
                            timeout=min(0.10, max(0.01, timeout_seconds - elapsed))
                        )
                        status = (
                            "cancelled"
                            if self._cancel_requested.is_set()
                            else "success" if returncode == 0 else "error"
                        )
                        break
                    except subprocess.TimeoutExpired:
                        continue
            finally:
                if process is not None and process.poll() is not None:
                    with self._lock:
                        if self._active is process:
                            self._active = None
                    self._cancel_requested.clear()

            stdout = self._read_tail(stdout_file, _STDOUT_LIMIT)
            stderr = self._read_tail(stderr_file, _STDERR_LIMIT)

        elapsed = time.monotonic() - started
        return PandocProcessResult(
            status,
            args,
            returncode,
            stdout,
            stderr,
            elapsed,
        )

    @staticmethod
    def _read_tail(handle, limit: int) -> str:
        handle.flush()
        size = os.fstat(handle.fileno()).st_size
        handle.seek(max(0, size - limit))
        return handle.read(limit).decode("utf-8", errors="replace")

    def cancel_active(self) -> bool:
        with self._lock:
            process = self._active
            if process is None or process.poll() is not None:
                return False
            self._cancel_requested.set()
        return self._terminate(process)

    def _terminate(self, process: subprocess.Popen) -> bool:
        if process.poll() is not None:
            return True
        try:
            if os.name == "nt":
                process.terminate()
            else:
                os.killpg(process.pid, signal.SIGTERM)
        except (OSError, ProcessLookupError):
            try:
                process.terminate()
            except OSError:
                pass
        try:
            process.wait(timeout=1.5)
            return True
        except subprocess.TimeoutExpired:
            pass
        try:
            if os.name == "nt":
                process.kill()
            else:
                os.killpg(process.pid, signal.SIGKILL)
        except (OSError, ProcessLookupError):
            try:
                process.kill()
            except OSError:
                pass
        try:
            process.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            return False
        return process.poll() is not None
