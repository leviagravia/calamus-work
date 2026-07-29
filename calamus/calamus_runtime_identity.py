"""GTK-free runtime identity and System Info rendering for Calamus."""
from __future__ import annotations

from dataclasses import dataclass


PRODUCT_NAME = "Calamus"


@dataclass(frozen=True)
class RuntimeIdentity:
    product_name: str
    build_label: str
    work_item: str
    published_baseline: str


@dataclass(frozen=True)
class SystemInfoSnapshot:
    identity: RuntimeIdentity
    python_version: str
    pygobject_version: str
    gtk_version: str
    operating_system: str
    desktop: str
    session: str
    config_path: str
    hunspell_dictionaries: str


def build_runtime_identity(
    build_label: str,
    work_item: str,
    published_baseline: str,
) -> RuntimeIdentity:
    return RuntimeIdentity(
        product_name=PRODUCT_NAME,
        build_label=build_label,
        work_item=work_item,
        published_baseline=published_baseline,
    )


def build_about_body(identity: RuntimeIdentity) -> str:
    """Return canonical About copy without importing GTK."""
    return f"""{identity.product_name}

Calamus is a lightweight text editor focused on plain-text writing.

It is designed for users who want more writing-oriented tools than a minimal editor, without the weight or complexity of a full IDE.

Main focus:
- fast plain-text editing
- clean writing workflow
- low-distraction interface
- useful tools for writers, students and note-takers
- offline-first usage

Key features:
- Find and replace
- Spell checking
- Recent files and favourites
- Clip Collection for reusable text blocks
- Clean Paste from PDF
- Paragraph reflow and line joining
- Smart typography tools
- Document statistics
- Focus and distraction-free modes
- Lightweight themes
- Research Panel with Markdown References, Tags, Source Notes and Scratchpad
- Quick Cite, Research Check and citation navigation
- Derived Research apparatus export
- Tags client with exact uses, navigation and previewed cross-authority maintenance
- An offline User Guide with practical workflows

What Calamus is not:
Calamus is not an IDE. It does not include code intelligence, LSP integration, heavy plugin systems, background indexing or cloud services.

This is intentional. Calamus is meant to remain simple, fast and focused on writing.

Recommended users:
- writers
- students
- Linux users who want a lightweight editor
- users who often copy text from PDFs
- users who prefer local, offline tools

Author: leviagravia@zohomail.eu"""


def render_system_info(snapshot: SystemInfoSnapshot) -> str:
    identity = snapshot.identity
    return "\n".join(
        (
            f"{identity.product_name}: {identity.build_label}",
            f"Work item: {identity.work_item}",
            f"Published baseline: {identity.published_baseline}",
            f"Python: {snapshot.python_version}",
            f"PyGObject: {snapshot.pygobject_version}",
            f"GTK: {snapshot.gtk_version}",
            f"OS: {snapshot.operating_system}",
            f"Desktop: {snapshot.desktop}",
            f"Session: {snapshot.session}",
            f"Config path: {snapshot.config_path}",
            f"Hunspell dictionaries: {snapshot.hunspell_dictionaries}",
        )
    )
