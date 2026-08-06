"""Test-only isolation helpers for the W101 true-App and desktop gates."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any


@dataclass(frozen=True)
class IsolatedRuntimePaths:
    home: Path
    config_home: Path
    data_home: Path
    cache_home: Path
    calamus_config_dir: Path


def runtime_paths(home: Path) -> IsolatedRuntimePaths:
    home = Path(home).resolve()
    config_home = home / ".config"
    data_home = home / ".local" / "share"
    cache_home = home / ".cache"
    return IsolatedRuntimePaths(
        home=home,
        config_home=config_home,
        data_home=data_home,
        cache_home=cache_home,
        calamus_config_dir=config_home / "calamus",
    )


def runtime_environment(paths: IsolatedRuntimePaths) -> dict[str, str]:
    return {
        "HOME": str(paths.home),
        "XDG_CONFIG_HOME": str(paths.config_home),
        "XDG_DATA_HOME": str(paths.data_home),
        "XDG_CACHE_HOME": str(paths.cache_home),
    }


def write_settings(config_dir: Path, workspace: Path, document: Path | None = None) -> Path:
    config_dir = Path(config_dir)
    config_dir.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "width": 900,
        "height": 650,
        "workspace_root": str(Path(workspace).resolve()),
        "workspace_visible": False,
        "last_file": str(Path(document).resolve()) if document is not None else None,
        "word_wrap": True,
        "line_numbers": False,
    }
    target = config_dir / "settings.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def snapshot_tree(root: Path) -> tuple[tuple[object, ...], ...]:
    """Return a deterministic, read-only snapshot without following symlinks."""
    root = Path(root)
    if not root.exists() and not root.is_symlink():
        return (("ABSENT",),)

    entries: list[tuple[object, ...]] = []
    for current, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        current_path = Path(current)
        dirnames.sort()
        filenames.sort()

        kept_dirs: list[str] = []
        for name in dirnames:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                entries.append(("SYMLINK", relative, os.readlink(path)))
            else:
                entries.append(("DIR", relative, stat.S_IMODE(info.st_mode)))
                kept_dirs.append(name)
        dirnames[:] = kept_dirs

        for name in filenames:
            path = current_path / name
            relative = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                entries.append(("SYMLINK", relative, os.readlink(path)))
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            entries.append(("FILE", relative, stat.S_IMODE(info.st_mode), info.st_size, digest))

    root_info = root.lstat()
    root_kind = "SYMLINK_ROOT" if stat.S_ISLNK(root_info.st_mode) else "ROOT"
    root_extra: object = os.readlink(root) if root_kind == "SYMLINK_ROOT" else stat.S_IMODE(root_info.st_mode)
    return ((root_kind, root_extra), *entries)
