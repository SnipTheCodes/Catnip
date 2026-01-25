from core.document.context import DocumentContext


class EditorController:
    """Handle editor-related events and coordinate updates with the document context."""

    def __init__(self, documents: DocumentContext):
        self.documents = documents

    def on_editor_text_changed(self, document_id: str, text: str) -> None:
        """Update document content and temp file when editor text changes."""

        document = self.documents.try_get(document_id)
        if not document:
            return

        if text != document.content:
            self.documents.mark_dirty(document_id, text)
            self.documents.write_temp(document_id)
