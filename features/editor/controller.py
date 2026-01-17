# features/editor/editor_controller.py
from core.document.context import DocumentContext


class EditorController:
    def __init__(self, documents: DocumentContext):
        self.documents = documents

    def on_editor_text_changed(self, document_id: str, text: str) -> None:
        document = self.documents.try_get(document_id)
        if not document:
            return

        if text != document.content:
            self.documents.mark_dirty(document_id, text)
            self.documents.write_temp(document_id)
