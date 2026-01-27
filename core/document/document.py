from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Document:
    """
    Represent an open document in the editor.

    A Document holds the in-memory state of a file, including its identity,
    display title, optional filesystem path, current text content, detected
    language, and dirty flag indicating unsaved changes.
    """
    id: str
    title: str
    path: Optional[Path]
    content: str
    language: str
    dirty: bool = False
