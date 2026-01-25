from pathlib import Path
from typing import Optional

from textual.widgets import TabbedContent
from textual.widgets import TextArea

from core.document.context import DocumentContext
from core.editor.languages import LANGUAGE_EXTENSION_MAP
from core.tab.constants import EXCEPTION_TAB_IDS
from core.theme import CUSTOM_EDITOR_THEMES


def register_custom_editor_theme(text_area: TextArea) -> None:
    for theme in CUSTOM_EDITOR_THEMES:
        text_area.register_theme(theme)


def get_runnable_file(tabbed_editor: TabbedContent,
                      documents: DocumentContext) -> Optional[Path]:
    active_tab = tabbed_editor.active_pane

    if not active_tab or active_tab.id in EXCEPTION_TAB_IDS:
        return None

    if not documents.is_document(active_tab.id):
        return None

    document = documents.get(active_tab.id)

    if not document.content.strip():
        return None

    # write and run temp file instead of forcing save
    return documents.write_temp(document.id)
