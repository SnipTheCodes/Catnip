from pathlib import Path
from typing import Callable, Optional

from textual.widgets import TabbedContent, TabPane

from core.document.context import DocumentContext
from core.document.document import Document
from core.explorer.dialogs import BaseDialogHandler
from core.tab.lifecycle import TabLifecycle


class FileWorkflow:
    """
    Coordinate file-related user workflows such as saving and closing documents.

    This class encapsulates high-level file operations that involve user
    interaction (dialogs and notifications) and document state management.
    It handles scenarios like prompting to save unsaved changes, saving to
    an existing path or a new path, and closing one or all tabs safely.

    FileWorkflow does not perform low-level file I/O itself; instead, it
    delegates persistence to DocumentContext and user interaction to the
    dialog handler, keeping responsibilities clearly separated.
    """

    def __init__(self, documents: DocumentContext, dialogs: BaseDialogHandler,
                 notify: Callable[[str], None]):
        self.documents = documents
        self.dialogs = dialogs
        self.notify = notify

    def close_active_tab(self, editor: TabbedContent,
                         tab_lifecycle: TabLifecycle) -> None:
        """Close the currently active tab, prompting to save if there are unsaved changes."""

        active_tab = editor.active_pane
        if not active_tab:
            return

        self.prompt_save_on_dirty(active_tab.id, tab_lifecycle)

        tab_lifecycle.on_tab_closed(active_tab.id)

        editor.remove_pane(active_tab.id)

    def prompt_to_save_all_before_exit(self, editor: TabbedContent,
                                       tab_lifecycle: TabLifecycle) -> None:
        """
        Prompt to save all open documents with unsaved changes before application exit.

        This method iterates over all open tabs and prompts the user to save
        any document that is dirty. It does not close tabs directly; it only
        ensures document state is safe before the application shuts down.

        Tabs are processed in reverse order so the most recently active tabs are
        handled first.
        """
        for tab in reversed(list(editor.query(TabPane))):
            editor.active = tab.id  # switch tab
            self.prompt_save_on_dirty(tab.id, tab_lifecycle)

    def prompt_save_on_dirty(self, tab_id: str,
                             tab_lifecycle: TabLifecycle) -> None:
        """
        Prompt the user to save the document for the given tab if it has unsaved changes.

        If the tab corresponds to a document with unsaved changes, the user is
        asked whether to save it. When confirmed, the document is saved, opening
        a file selection dialog only if the document does not yet have a path.
        """
        if not tab_lifecycle.needs_save_prompt(tab_id):
            return

        name = tab_lifecycle.get_display_name(tab_id)

        confirm = self.dialogs.confirm_action(
            title="Unsaved Changes",
            message=f"Do you want to save changes to {name}?"
        )

        if not confirm:
            return

        document = self.documents.get(tab_id)

        if document.path is None:
            file_path = self.dialogs.select_folder_save()
            if not file_path:
                return

            self.documents.save_to(document.id, file_path)
            self.documents.close(document.id)
            self.notify(f"File saved to {file_path}")
            return

        self.documents.save(document.id)
        self.notify(f"Saved {document.title}")

    def save_on_dirty(self, document: Document) -> None:
        """
        Save the given document if it has unsaved changes.

        This method unconditionally writes the document to its current path
        when it is dirty, and does nothing if the document is already clean.
        """

        if not self.documents.has_unsaved_changes(document.id):
            self.notify("Already up to date")
            return

        self.documents.save(document.id)
        self.notify(f"Saved {document.title}")

    def save_as(self, document: Document) -> Optional[Path]:
        """
        Save the given document to a new user-selected location.

        The user is prompted to choose a destination path. If the user cancels
        the dialog, no save is performed and None is returned.

        Returns:
            The new file path if the save succeeds; otherwise, None.
        """
        file_path = self.dialogs.select_folder_save()
        if not file_path:
            return None

        self.documents.save_to(document.id, file_path)
        self.notify(f"File saved to {file_path}")

        return file_path
