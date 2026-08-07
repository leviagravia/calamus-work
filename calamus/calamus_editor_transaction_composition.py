"""W103 construction boundary for editor transaction ownership."""
from __future__ import annotations

from calamus_application_components import (
    EditorTransactionCompositionInput,
    EditorTransactionComponents,
)
from calamus_editor_buffer_adapter import EditorBufferAdapter
from calamus_editor_transaction import EditorTransactionController


def build_editor_transaction_components(
    inputs: EditorTransactionCompositionInput,
) -> EditorTransactionComponents:
    adapter = EditorBufferAdapter(inputs.text_view)
    controller = EditorTransactionController(
        session=inputs.document_session,
        session_controller=inputs.document_session_controller,
        history_runtime=inputs.history_runtime,
        buffer_adapter=adapter,
    )
    return EditorTransactionComponents(
        controller=controller,
        buffer_adapter=adapter,
    )
