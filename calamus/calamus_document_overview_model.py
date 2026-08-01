"""GTK-free presentation values for W96 Document Overview Core."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

DOCUMENT_OVERVIEW_CATEGORIES = (
    ("overview", "Overview"),
    ("structure", "Structure"),
    ("research", "Research"),
    ("integrity", "Integrity"),
    ("statistics", "Statistics"),
)

@dataclass(frozen=True)
class DocumentOverviewRow:
    id: str
    kind: str
    title: str
    subtitle: str
    payload: Any

    def __post_init__(self) -> None:
        if not all(isinstance(value, str) and value for value in (self.id, self.kind, self.title)):
            raise ValueError("overview row identity, kind and title are required")
        if not isinstance(self.subtitle, str):
            raise TypeError("overview row subtitle must be str")
