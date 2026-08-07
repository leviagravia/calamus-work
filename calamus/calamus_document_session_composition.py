"""Local W102 builder for the authoritative document session."""
from __future__ import annotations

from calamus_application_components import (
    DocumentSessionComponents,
    DocumentSessionCompositionInput,
)
from calamus_document_session import DocumentSession
from calamus_document_session_controller import (
    DocumentSessionController,
    DocumentSessionPorts,
)
from calamus_model import Document


def build_document_session_components(
    inputs: DocumentSessionCompositionInput,
) -> DocumentSessionComponents:
    session = DocumentSession(Document(file_path=inputs.initial_file_path))
    controller = DocumentSessionController(
        session,
        DocumentSessionPorts(
            read_buffer_text=inputs.read_buffer_text,
            replace_buffer_text=inputs.replace_buffer_text,
            reset_undo_history=inputs.reset_undo_history,
            read_text_file=inputs.read_text_file,
            write_text_file=inputs.write_text_file,
            is_large_text_file=inputs.is_large_text_file,
        ),
    )
    return DocumentSessionComponents(session=session, controller=controller)
