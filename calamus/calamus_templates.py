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


@dataclass(frozen=True)
class ManagedTemplateEntry:
    """A regular template exposed by the manager UI."""

    name: str
    path: str
    protected: bool = False


def list_managed_templates(config_dir: str) -> list[ManagedTemplateEntry]:
    """List direct regular templates, excluding symbolic links.

    ``blank-note.txt`` is the store-owned default.  Its contents may be
    overwritten through Save as Template, but its stable name is protected
    because :func:`ensure_templates_dir` recreates it whenever it is missing.
    """
    templates_dir = ensure_templates_dir(config_dir)
    items: list[ManagedTemplateEntry] = []
    for name in sorted(os.listdir(templates_dir), key=str.casefold):
        full = os.path.abspath(os.path.join(templates_dir, name))
        if os.path.islink(full):
            continue
        if os.path.isfile(full) and is_supported_template_path(name):
            items.append(
                ManagedTemplateEntry(
                    name=name,
                    path=full,
                    protected=name == DEFAULT_TEMPLATE_NAME,
                )
            )
    return items


def list_templates(config_dir: str) -> list[tuple[str, str]]:
    """List regular supported templates for the dynamic New submenu."""
    return [(entry.name, entry.path) for entry in list_managed_templates(config_dir)]


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

@dataclass(frozen=True)
class RenameTemplatePlan:
    """Immutable direct-child rename within the canonical template store."""

    store_dir: str
    source_path: str
    target_path: str
    source_name: str
    target_name: str


@dataclass(frozen=True)
class DeleteTemplatePlan:
    """Immutable deletion of one user-owned template."""

    store_dir: str
    target_path: str
    target_name: str


def _validate_template_filename(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("template name must be a string")
    normalized = name.strip()
    if not normalized or normalized in (".", ".."):
        raise ValueError("Template name must not be empty")
    if normalized != os.path.basename(normalized) or "/" in normalized or "\\" in normalized:
        raise ValueError("Template name must not contain a folder path")
    if not is_supported_template_path(normalized):
        raise ValueError("Template name must end in .txt or .md")
    return normalized


def _validate_managed_template_source(store_dir: str, path: str) -> tuple[str, str]:
    if not isinstance(path, str):
        raise TypeError("template path must be a string")
    if path == "":
        raise ValueError("template path must not be empty")
    normalized = os.path.abspath(os.path.expanduser(path))
    if os.path.dirname(normalized) != store_dir:
        raise ValueError("Template is outside the Calamus templates folder")
    name = os.path.basename(normalized)
    _validate_template_filename(name)
    if os.path.islink(normalized) or not os.path.isfile(normalized):
        raise ValueError("Template must be a regular file and not a symbolic link")
    return normalized, name


def _fsync_template_store(store_dir: str) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        directory_fd = os.open(store_dir, flags)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError:
        # The filesystem mutation has already committed.  Directory fsync is
        # a best-effort durability enhancement, not a reason to report a false
        # application-level failure after success.
        pass


def prepare_rename_template_plan(
    config_dir: str,
    source_path: str,
    new_name: str | None,
) -> RenameTemplatePlan | None:
    """Validate a no-overwrite rename inside the canonical template store."""
    if new_name is None:
        return None
    store_dir = ensure_templates_dir(config_dir)
    source_path, source_name = _validate_managed_template_source(store_dir, source_path)
    if source_name == DEFAULT_TEMPLATE_NAME:
        raise ValueError("The default blank-note.txt template cannot be renamed")
    target_name = _validate_template_filename(new_name)
    if target_name == source_name:
        return None
    target_path = os.path.abspath(os.path.join(store_dir, target_name))
    if os.path.dirname(target_path) != store_dir:
        raise ValueError("Template target is outside the Calamus templates folder")
    if os.path.lexists(target_path):
        raise FileExistsError(f"A template named '{target_name}' already exists")
    return RenameTemplatePlan(
        store_dir=store_dir,
        source_path=source_path,
        target_path=target_path,
        source_name=source_name,
        target_name=target_name,
    )


def rename_template_file(plan: RenameTemplatePlan) -> str:
    """Apply a validated no-overwrite rename and return the new path."""
    if not isinstance(plan, RenameTemplatePlan):
        raise TypeError("plan must be a RenameTemplatePlan")
    store_dir = os.path.abspath(plan.store_dir)
    source_path, source_name = _validate_managed_template_source(store_dir, plan.source_path)
    if source_name == DEFAULT_TEMPLATE_NAME:
        raise ValueError("The default blank-note.txt template cannot be renamed")
    target_name = _validate_template_filename(plan.target_name)
    target_path = os.path.abspath(plan.target_path)
    if source_path != os.path.abspath(plan.source_path):
        raise ValueError("Template source does not match its validated plan")
    if target_path != os.path.abspath(os.path.join(store_dir, target_name)):
        raise ValueError("Template target does not match its validated plan")
    if os.path.dirname(target_path) != store_dir:
        raise ValueError("Template target is outside the Calamus templates folder")
    if os.path.lexists(target_path):
        raise FileExistsError(f"A template named '{target_name}' already exists")
    os.rename(source_path, target_path)
    _fsync_template_store(store_dir)
    return target_path


def prepare_delete_template_plan(config_dir: str, target_path: str) -> DeleteTemplatePlan:
    """Validate deletion of one non-default regular template."""
    store_dir = ensure_templates_dir(config_dir)
    target_path, target_name = _validate_managed_template_source(store_dir, target_path)
    if target_name == DEFAULT_TEMPLATE_NAME:
        raise ValueError("The default blank-note.txt template cannot be deleted")
    return DeleteTemplatePlan(
        store_dir=store_dir,
        target_path=target_path,
        target_name=target_name,
    )


def delete_template_file(plan: DeleteTemplatePlan) -> str:
    """Delete one validated template and return its former path."""
    if not isinstance(plan, DeleteTemplatePlan):
        raise TypeError("plan must be a DeleteTemplatePlan")
    store_dir = os.path.abspath(plan.store_dir)
    target_path, target_name = _validate_managed_template_source(store_dir, plan.target_path)
    if target_name == DEFAULT_TEMPLATE_NAME:
        raise ValueError("The default blank-note.txt template cannot be deleted")
    if target_path != os.path.abspath(plan.target_path):
        raise ValueError("Template target does not match its validated plan")
    if target_name != plan.target_name:
        raise ValueError("Template name does not match its validated plan")
    os.unlink(target_path)
    _fsync_template_store(store_dir)
    return target_path
