from core.document.context import DocumentContext
from core.tab.constants import EXCEPTION_TAB_IDS


class TabLifecycle:
    """
    Application-level policy for tab lifecycle decisions.

    This class does NOT manipulate UI widgets.
    It coordinates between tab identity and document state.
    """

    def __init__(self, documents: DocumentContext):
        self.documents = documents

    def is_document_tab(self, tab_id: str) -> bool:
        return self.documents.is_document(tab_id)

    def needs_save_prompt(self, tab_id: str) -> bool:
        """Return True if closing this tab should prompt the user to save."""

        if tab_id in EXCEPTION_TAB_IDS:
            return False

        if not self.documents.is_document(tab_id):
            return False

        return self.documents.has_unsaved_changes(tab_id)

    def get_display_name(self, tab_id: str) -> str:
        """Human-friendly name used in confirmation dialogs."""

        document = self.documents.try_get(tab_id)
        if not document:
            return "this tab"

        return document.title if document.path else "this untitled document"

    def on_tab_closed(self, tab_id: str) -> None:
        """Notify DocumentContext that a tab has been closed."""
        
        if self.documents.is_document(tab_id):
            self.documents.close(tab_id)
