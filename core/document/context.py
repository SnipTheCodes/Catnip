import hashlib
from pathlib import Path
from typing import Dict, Optional

from features.editor.constants import LANGUAGES
from .document import Document


class DocumentContext:
    def __init__(self) -> None:
        self._documents: Dict[str, Document] = {}

    def open(self, path: Path) -> Document:
        path = path.resolve()
        doc_id = self._id_from_path(path)

        if doc_id in self._documents:
            return self._documents[doc_id]

        content = path.read_text(encoding="utf-8")

        doc = Document(
            id=doc_id,
            title=path.name,
            path=path,
            content=content,
            language=self._resolve_language(path.suffix.lstrip(".")),
            dirty=False,
        )

        self._documents[doc_id] = doc
        return doc

    def create_untitled(self) -> Document:
        doc_id = self._new_untitled_id()

        doc = Document(
            id=doc_id,
            title="Untitled",
            path=None,
            content="",
            language="markdown",
            dirty=False,
        )

        self._documents[doc_id] = doc
        return doc

    def get(self, doc_id: str) -> Document:
        return self._documents[doc_id]

    def mark_dirty(self, doc_id: str, content: str) -> None:
        doc = self._documents[doc_id]
        doc.content = content
        doc.dirty = True

    def save(self, doc_id: str, path: Optional[Path] = None) -> None:
        doc = self._documents[doc_id]

        if path:
            doc.path = path
            doc.title = path.name

        if not doc.path:
            raise ValueError("Document has no path")

        doc.path.write_text(doc.content, encoding="utf-8")
        doc.dirty = False

    def save_as(self, document_id: str, new_path: Path) -> Document:
        """
        Save a document to a new file path and return a new document instance.

        The original document remains unchanged.
        """
        source = self.get(document_id)

        new_path = new_path.resolve()
        new_path.parent.mkdir(parents=True, exist_ok=True)

        # write content
        new_path.write_text(source.content, encoding="utf-8")

        new_doc_id = self._id_from_path(new_path)

        new_doc = Document(
            id=new_doc_id,
            title=new_path.name,
            path=new_path,
            content=source.content,
            language=self._resolve_language(new_path.suffix.lstrip(".")),
            dirty=False,
        )

        self._documents[new_doc_id] = new_doc
        return new_doc

    def close(self, doc_id: str) -> None:
        self._documents.pop(doc_id, None)

    def close_by_path(self, path: Path) -> list[str]:
        """
        Close all open documents matching the given file path and return their IDs.
        """
        closed = []
        for doc_id, doc in list(self._documents.items()):
            if doc.path == path:
                self.close(doc_id)
                closed.append(doc_id)
        return closed

    def _resolve_language(self, suffix: str) -> str:
        """
        Resolve file suffix to a supported Textual TextArea language.

        Falls back to 'markdown' if the language is not supported.
        """
        try:
            from textual.widgets import TextArea
            supported = set(LANGUAGES)
        except Exception:
            supported = set()

        lang = suffix.lower()
        return lang if lang in supported else "markdown"

    def _id_from_path(self, path: Path) -> str:
        digest = hashlib.sha1(str(path).encode()).hexdigest()[:8]
        return f"doc-{digest}"

    def _new_untitled_id(self) -> str:
        index = len(self._documents) + 1
        return f"doc-untitled-{index}"
