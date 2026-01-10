import re
from pathlib import Path
from typing import Union

from textual.widgets import TabPane, TextArea


def get_tab_id_from_path(file_path: Union[str, Path]) -> str:
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return re.sub(r"[^a-zA-Z0-9]", "-", file_path.name).lower()


def untitled_tab_has_content(tab: TabPane) -> bool:
    return tab.id.startswith("untitled") and tab.query_one(TextArea).text.strip()
