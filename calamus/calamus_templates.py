"""Template discovery, loading, and new-document planning for Calamus.

GTK menu construction, save prompts, Gtk.TextBuffer mutation, document identity
commit, Undo reset, title updates, and error dialogs remain owned by the App
boundary.  This module owns the template store and the deterministic transition
from template text to a new untitled document.
"""
from __future__ import annotations

from dataclasses import dataclass
import os

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
