from pathlib import Path
from typing import Callable, Optional

from textual.widgets import TabbedContent, TabPane

from core.document.context import DocumentContext
from core.document.document import Document
from core.explorer.dialogs import BaseDialogHandler
from core.tab.lifecycle import TabLifecycle


class FileWorkflow:
    def __init__(self, documents: DocumentContext, dialogs: BaseDialogHandler,
                 notify: Callable[[str], None]):
        self.documents = documents
        self.dialogs = dialogs
        self.notify = notify

    def prompt_and_save(self, document: Document) -> bool:
        if document.path is None:
            file_path = self.dialogs.select_folder_save()
            if not file_path:
                return False

            self.documents.save_as(document.id, file_path)
            self.notify(f"File saved to {file_path}")
            return True

        self.documents.save(document.id)
        self.notify("File saved!")
        return True

    def close_active_tab(self, editor: TabbedContent,
                         tab_lifecycle: TabLifecycle) -> None:
        active_tab = editor.active_pane
        if not active_tab:
            return

        if tab_lifecycle.needs_save_prompt(active_tab.id):
            name = tab_lifecycle.get_display_name(active_tab.id)

            confirm = self.dialogs.confirm_action(title="Unsaved Changes",
                                                  message=f"Do you want to save changes to {name}?")

            if confirm and not self.prompt_and_save(
                    self.documents.get(active_tab.id)):
                return

        tab_lifecycle.on_tab_closed(active_tab.id)
        editor.remove_pane(active_tab.id)

    def confirm_and_close_all_tabs(self, editor: TabbedContent,
                                   tab_lifecycle: TabLifecycle) -> None:
        # iterate over open panes in reverse order (last active first)
        for tab in reversed(list(editor.query(TabPane))):
            if tab_lifecycle.needs_save_prompt(tab.id):
                name = tab_lifecycle.get_display_name(tab.id)
                editor.active = tab.id

                confirm = self.dialogs.confirm_action(title="Unsaved Changes",
                                                      message=f"Do you want to save changes to {name}?")
                if confirm and not self.prompt_and_save(
                        self.documents.get(tab.id)):
                    return
            tab_lifecycle.on_tab_closed(tab.id)

    def save_existing_document(self, document: Document) -> None:
        if not self.documents.has_unsaved_changes(document.id):
            return

        self.documents.save(document.id)

    def save_as(self, document: Document) -> Optional[Path]:
        file_path = self.dialogs.select_folder_save()
        if not file_path:
            return None

        self.documents.save_as(document.id, file_path)
        return file_path
