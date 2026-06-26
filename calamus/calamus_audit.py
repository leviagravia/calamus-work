"""Lightweight audit helpers for Calamus release/selftest checks."""
from __future__ import annotations

import os
import py_compile
import tempfile
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class ShortcutSpec:
    command: str
    shortcut: str
    menu: str = ""
    reserved_note: str = ""


def _load_shortcuts() -> tuple[ShortcutSpec, ...]:
    from calamus_shortcuts import SHORTCUTS as REGISTRY_SHORTCUTS, display_to_accelerator

    specs = []
    for item in REGISTRY_SHORTCUTS:
        if item.shortcut in {"menu", "automatic"} or item.shortcut.startswith("Drop "):
            continue
        # Audit should see the exact accelerator tokens used by GTK. Aggregate
        # display rows expose their primary shortcut in audit metadata.
        primary = item.shortcut.split(" / ")[0].strip()
        if ".." in primary:
            continue
        specs.append(ShortcutSpec(item.command, display_to_accelerator(primary), item.menu, getattr(item, "note", "")))
    return tuple(specs)


SHORTCUTS: tuple[ShortcutSpec, ...] = _load_shortcuts()


def shortcut_conflicts(shortcuts: Iterable[ShortcutSpec] = SHORTCUTS) -> dict[str, list[str]]:
    seen: dict[str, list[str]] = {}
    for spec in shortcuts:
        key = normalize_shortcut(spec.shortcut)
        seen.setdefault(key, []).append(spec.command)
    return {key: names for key, names in seen.items() if len(names) > 1}


def normalize_shortcut(shortcut: str) -> str:
    # Normalize common aliases without depending on GTK.
    return (shortcut or "").replace("<Ctrl>", "<Control>").strip()


def shortcut_warnings(shortcuts: Iterable[ShortcutSpec] = SHORTCUTS) -> list[str]:
    warnings: list[str] = []
    for spec in shortcuts:
        if spec.reserved_note:
            warnings.append(f"{spec.command} {spec.shortcut}: {spec.reserved_note}")
    return warnings



def default_package_paths() -> tuple[str, ...]:
    """Return the installed Calamus paths that should be audited.

    The audit must be scoped to Calamus only.  The previous 5.4 selftest
    accidentally walked /usr, which made results depend on unrelated system
    packages installed on the user's machine.
    """
    paths = [
        "/usr/bin/calamus",
        "/usr/bin/calamus-selftest",
        "/usr/lib/calamus",
        "/usr/share/calamus",
    ]
    return tuple(path for path in paths if os.path.exists(path))


def dev_package_paths(anchor: str) -> tuple[str, ...]:
    """Return Calamus paths in an unpacked/development package tree."""
    root = os.path.abspath(anchor)
    candidates = [
        os.path.join(root, "usr", "bin", "calamus"),
        os.path.join(root, "usr", "bin", "calamus-selftest"),
        os.path.join(root, "usr", "lib", "calamus"),
        os.path.join(root, "usr", "share", "calamus"),
    ]
    return tuple(path for path in candidates if os.path.exists(path))


def iter_python_files(paths: Iterable[str]) -> Iterable[str]:
    """Yield Python source files from files/directories in paths."""
    for root in paths:
        if os.path.isfile(root):
            if root.endswith(".py") or os.access(root, os.X_OK):
                yield root
            continue
        for dirpath, _dirnames, filenames in os.walk(root):
            for filename in filenames:
                path = os.path.join(dirpath, filename)
                if filename.endswith(".py") or (filename.startswith("calamus") and os.access(path, os.X_OK)):
                    yield path

def compile_python_paths(paths: Iterable[str]) -> list[tuple[str, str]]:
    """Compile Calamus Python sources. Return [(path, error)] failures."""
    failures: list[tuple[str, str]] = []
    for path in iter_python_files(paths):
        try:
            # Compile to a temporary file so selftest does not leave __pycache__
            # artifacts in installed package trees.
            with tempfile.NamedTemporaryFile(suffix=".pyc") as tmp:
                py_compile.compile(path, cfile=tmp.name, doraise=True)
        except (py_compile.PyCompileError, OSError) as exc:
            failures.append((path, str(exc)))
    return failures


def compile_python_tree(root: str) -> list[tuple[str, str]]:
    """Compatibility wrapper: compile Python files below one root."""
    return compile_python_paths((root,))


def find_pycache_dirs_in_paths(paths: Iterable[str]) -> list[str]:
    hits: list[str] = []
    for root in paths:
        if os.path.isfile(root):
            continue
        for dirpath, dirnames, _filenames in os.walk(root):
            for dirname in dirnames:
                if dirname == "__pycache__":
                    # Runtime Python caches may be created after installation under /usr.
                    # They are not shipped by the .deb, so installed selftests should
                    # not fail because Python generated them while importing Calamus.
                    if os.path.abspath(dirpath).startswith("/usr/"):
                        continue
                    hits.append(os.path.join(dirpath, dirname))
    return hits


def find_pycache_dirs(root: str) -> list[str]:
    """Compatibility wrapper: find __pycache__ below one root."""
    return find_pycache_dirs_in_paths((root,))
