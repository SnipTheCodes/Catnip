from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class Document:
    id: str
    title: str
    path: Optional[Path]
    content: str
    language: str
    dirty: bool = False
