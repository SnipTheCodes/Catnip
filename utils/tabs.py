import hashlib
import re
from pathlib import Path
from typing import Union

from textual.widgets import TabPane, TextArea, TabbedContent

from core.editor.languages import LANGUAGE_EXTENSION_MAP


def get_tab_id_from_path(file_path: Union[str, Path]) -> str:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return re.sub(r"[^a-zA-Z0-9]", "-", file_path.name).lower()


def id_from_path(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    return f"doc-{digest}"


def untitled_tab_has_content(tab: TabPane) -> bool:
    return tab.id.startswith("untitled") and tab.query_one(
        TextArea).text.strip()


def temp_file_suffix(language: str) -> str:
    return "." + LANGUAGE_EXTENSION_MAP.get(language, "tmp")


def is_open(tab_id: str, editor: TabbedContent) -> bool:
    return any(pane.id == tab_id for pane in editor.query(TabPane))
