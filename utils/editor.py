from enum import Enum
from pathlib import Path
from typing import Optional

from textual.widgets import TabbedContent
from textual.widgets import TextArea

from core.document.context import DocumentContext
from core.tab.constants import EXCEPTION_TAB_IDS
from core.theme import CUSTOM_EDITOR_THEMES


class RunnableLanguage(Enum):
    """
    Languages supported for execution by Catnip.

    This enum defines the set of file extensions that can be run.
    For each language added here, a corresponding runner
    implementation must exist in @features/executor/runner.

    This keeps the list of runnable languages explicit and centralized.
    """
    PY = "py"
    JS = "js"
    TS = "ts"
    JAVA = "java"


def register_custom_editor_theme(text_area: TextArea) -> None:
    for theme in CUSTOM_EDITOR_THEMES:
        text_area.register_theme(theme)


def prepare_runnable_file(tabbed_editor: TabbedContent,
                          documents: DocumentContext) -> Optional[Path]:
    """
    Determine whether the currently active tab can be executed and, if so,
    prepare a temporary file for execution.

    This function encapsulates the editor-side rules for running a file
    (which tab is eligible, whether it maps to a document, and whether its
    language is supported) and hides these details from the runner.

    @Returns:
        A Path to a temporary file ready to execute if the active tab is runnable;
        otherwise, None.
    """

    active_tab = tabbed_editor.active_pane

    if not active_tab or active_tab.id in EXCEPTION_TAB_IDS:
        return None

    if not documents.is_document(active_tab.id):
        return None

    document = documents.get(active_tab.id)

    if not document.content.strip():
        return None

    suffix = (
        document.path.suffix.lstrip(".")
        if document.path
        else document.language
    )
    try:
        RunnableLanguage(suffix)
    except ValueError:
        return None

    # write and run temp file instead of forcing save
    return documents.write_temp(document.id)
