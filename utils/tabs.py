import hashlib
from pathlib import Path

from textual.widgets import TabPane, TabbedContent


def id_from_path(path: Path) -> str:
    digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
    return f"doc-{digest}"


def is_open(tab_id: str, editor: TabbedContent) -> bool:
    return any(pane.id == tab_id for pane in editor.query(TabPane))
