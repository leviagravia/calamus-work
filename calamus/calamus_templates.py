"""Template discovery, loading, and new-document planning for Calamus.

GTK menu construction, save prompts, Gtk.TextBuffer mutation, document identity
commit, Undo reset, title updates, and error dialogs remain owned by the App
boundary.  This module owns the template store and the deterministic transition
from template text to a new untitled document.
"""
from __future__ import annotations

from dataclasses import dataclass
import os
import stat
import tempfile

SUPPORTED_TEMPLATE_SUFFIXES = (".txt", ".md")
DEFAULT_TEMPLATE_NAME = "blank-note.txt"
DEFAULT_TEMPLATE_TEXT = "Title\n=====\n\n"


@dataclass(frozen=True)
class NewFromTemplatePlan:
    """Immutable transition from a template source to an untitled document."""

    source_path: str
    text: str
    target_path: None = None
    modified: bool = True


def ensure_templates_dir(config_dir: str) -> str:
    """Return the user template directory, creating the default template."""
    if not isinstance(config_dir, str):
        raise TypeError("config_dir must be a string")
    if config_dir == "":
        raise ValueError("config_dir must not be empty")
    path = os.path.abspath(os.path.join(config_dir, "templates"))
    os.makedirs(path, exist_ok=True)
    sample = os.path.join(path, DEFAULT_TEMPLATE_NAME)
    if not os.path.exists(sample):
        with open(sample, "w", encoding="utf-8") as handle:
            handle.write(DEFAULT_TEMPLATE_TEXT)
    return path


def is_supported_template_path(path: str) -> bool:
    """Return whether *path* has a supported document-template suffix."""
    return isinstance(path, str) and path.lower().endswith(SUPPORTED_TEMPLATE_SUFFIXES)


def list_templates(config_dir: str) -> list[tuple[str, str]]:
    """List regular supported template files from the canonical store."""
    templates_dir = ensure_templates_dir(config_dir)
    items: list[tuple[str, str]] = []
    for name in sorted(os.listdir(templates_dir)):
        full = os.path.abspath(os.path.join(templates_dir, name))
        if os.path.isfile(full) and is_supported_template_path(name):
            items.append((name, full))
    return items


def read_template(path: str) -> str:
    """Read a supported regular template file as UTF-8 text."""
    if not isinstance(path, str):
        raise TypeError("template path must be a string")
    if path == "":
        raise ValueError("template path must not be empty")
    normalized = os.path.abspath(os.path.expanduser(path))
    if not is_supported_template_path(normalized):
        raise ValueError("template must be a .txt or .md file")
    if not os.path.isfile(normalized):
        raise FileNotFoundError(f"Template is not a regular file: {normalized}")
    with open(normalized, "r", encoding="utf-8") as handle:
        return handle.read()


def prepare_new_from_template_plan(template_path: str, text: str) -> NewFromTemplatePlan:
    """Describe a new unsaved document derived from already-read template text."""
    if not isinstance(template_path, str):
        raise TypeError("template_path must be a string")
    if template_path == "":
        raise ValueError("template_path must not be empty")
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    normalized = os.path.abspath(os.path.expanduser(template_path))
    if not is_supported_template_path(normalized):
        raise ValueError("template must be a .txt or .md file")
    return NewFromTemplatePlan(source_path=normalized, text=text)


@dataclass(frozen=True)
class SaveTemplatePlan:
    """Immutable copy-to-template-store plan for the active buffer."""

    store_dir: str
    target_path: str
    text: str
    replaces_existing: bool


def suggest_template_filename(current_file: str | None) -> str:
    """Return a safe direct-child filename suggestion for the save dialog."""
    if current_file is not None and not isinstance(current_file, str):
        raise TypeError("current_file must be a string or None")
    basename = os.path.basename(current_file) if current_file else ""
    if not basename or basename in (".", ".."):
        return "template.txt"
    stem, suffix = os.path.splitext(basename)
    if suffix.lower() in SUPPORTED_TEMPLATE_SUFFIXES:
        return basename
    stem = stem or "template"
    return f"{stem}.txt"


def prepare_save_template_plan(
    config_dir: str,
    selected_path: str | None,
    text: str,
) -> SaveTemplatePlan | None:
    """Validate an accepted destination inside the canonical template store.

    The chooser, overwrite confirmation, active-buffer read, menu refresh,
    notifications, and document state remain App responsibilities.  The target
    must be a direct child of the canonical store and must use a supported
    suffix.  Existing symlinks and non-regular targets are rejected.
    """
    if selected_path is None or selected_path == "":
        return None
    if not isinstance(selected_path, str):
        raise TypeError("selected_path must be a string or None")
    if not isinstance(text, str):
        raise TypeError("text must be a string")

    templates_dir = ensure_templates_dir(config_dir)
    target_path = os.path.abspath(os.path.expanduser(selected_path))
    target_parent = os.path.dirname(target_path)
    if target_parent != templates_dir:
        raise ValueError("Template must be saved directly in the Calamus templates folder")

    name = os.path.basename(target_path)
    if not name or name in (".", ".."):
        raise ValueError("Template filename must not be empty")
    if not is_supported_template_path(name):
        raise ValueError("Template filename must end in .txt or .md")

    replaces_existing = os.path.lexists(target_path)
    if replaces_existing and (os.path.islink(target_path) or not os.path.isfile(target_path)):
        raise ValueError("Template target must be a regular file and not a symbolic link")

    return SaveTemplatePlan(
        store_dir=templates_dir,
        target_path=target_path,
        text=text,
        replaces_existing=replaces_existing,
    )


def write_template_atomic(plan: SaveTemplatePlan) -> str:
    """Write *plan* atomically in its existing canonical store directory."""
    if not isinstance(plan, SaveTemplatePlan):
        raise TypeError("plan must be a SaveTemplatePlan")

    target_path = plan.target_path
    parent = os.path.dirname(target_path)
    if parent != plan.store_dir:
        raise ValueError("Template target is outside its canonical store")
    if not os.path.isdir(parent):
        raise FileNotFoundError(f"Template folder is not available: {parent}")
    if os.path.lexists(target_path) and (
        os.path.islink(target_path) or not os.path.isfile(target_path)
    ):
        raise ValueError("Template target must be a regular file and not a symbolic link")

    existing_mode = None
    if os.path.isfile(target_path) and not os.path.islink(target_path):
        existing_mode = stat.S_IMODE(os.stat(target_path, follow_symlinks=False).st_mode)

    fd, temporary_path = tempfile.mkstemp(
        prefix=".calamus-template-",
        suffix=".tmp",
        dir=parent,
        text=True,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(plan.text)
            handle.flush()
            os.fsync(handle.fileno())
        if existing_mode is not None:
            os.chmod(temporary_path, existing_mode)
        os.replace(temporary_path, target_path)
        temporary_path = ""

        directory_flags = os.O_RDONLY
        if hasattr(os, "O_DIRECTORY"):
            directory_flags |= os.O_DIRECTORY
        try:
            directory_fd = os.open(parent, directory_flags)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError:
            # The file replacement has already committed. Directory fsync is a
            # best-effort durability enhancement and must not report a false
            # application-level failure after a successful atomic replace.
            pass
        return target_path
    finally:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
