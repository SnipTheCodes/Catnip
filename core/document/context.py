from pathlib import Path
from typing import Dict, Optional

from core.editor.languages import resolve_language
from utils.tabs import id_from_path, temp_file_suffix
from .document import Document


class DocumentContext:
    def __init__(self) -> None:
        self._documents: Dict[str, Document] = {}
        self._temp_dir = Path.home() / ".catnip/tmp"
        self._temp_dir.mkdir(parents=True, exist_ok=True)

    def open(self, path: Path) -> Document:
        path = path.resolve()
        doc_id = id_from_path(path)

        if doc_id in self._documents:
            return self._documents[doc_id]

        content = path.read_text(encoding="utf-8")

        doc = Document(id=doc_id, title=path.name, path=path, content=content,
                       language=resolve_language(path.suffix.lstrip(".")),
                       dirty=False, )

        self._documents[doc_id] = doc
        return doc

    def create_untitled(self) -> Document:
        doc_id = self._new_untitled_id()

        doc = Document(id=doc_id, title="Untitled", path=None, content="",
                       language="markdown", dirty=False, )

        self._documents[doc_id] = doc
        return doc

    def get_temp_path(self, doc_id: str) -> Path:
        """
        Return the temp file path for a document.
        """
        language = self._documents[doc_id].language
        return self._temp_dir / f"{doc_id}{temp_file_suffix(language)}"

    def write_temp(self, doc_id: str) -> Path:
        """
        Write the document content to a temp file and return its path.
        """
        doc = self._documents[doc_id]
        temp_path = self.get_temp_path(doc_id)
        temp_path.write_text(doc.content, encoding="utf-8")
        return temp_path

    def remove_temp(self, doc_id: str) -> None:
        """
        Remove the temp file associated with the document if it exists.
        """
        temp_path = self.get_temp_path(doc_id)
        if temp_path.exists():
            temp_path.unlink()

    def get(self, doc_id: str) -> Document:
        return self._documents[doc_id]

    def try_get(self, doc_id: str) -> Optional[Document]:
        """
        Return the document with the given ID, or None if it does not exist.
        """
        return self._documents.get(doc_id)

    def is_document(self, doc_id: str) -> bool:
        """
        Return True if the given ID refers to a managed document.
        """
        return doc_id in self._documents

    def mark_dirty(self, doc_id: str, content: str) -> None:
        doc = self._documents[doc_id]
        doc.content = content
        doc.dirty = True

    def has_unsaved_changes(self, doc_id: str) -> bool:
        """
        Return True if the document exists and has unsaved changes.
        """
        doc = self._documents.get(doc_id)
        return bool(doc and doc.dirty)

    def save(self, doc_id: str, path: Optional[Path] = None) -> None:
        doc = self._documents[doc_id]

        if path:
            doc.path = path
            doc.title = path.name

        if not doc.path:
            raise ValueError("Document has no path")

        doc.path.write_text(doc.content, encoding="utf-8")
        doc.dirty = False
        self.remove_temp(doc_id)

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

        new_doc_id = id_from_path(new_path)

        new_doc = Document(id=new_doc_id, title=new_path.name,
                           path=new_path, content=source.content,
                           language=resolve_language(
                               new_path.suffix.lstrip(".")), dirty=False, )

        self._documents[new_doc_id] = new_doc
        return new_doc

    def close(self, doc_id: str) -> None:
        self.remove_temp(doc_id)
        self._documents.pop(doc_id, None)

    def should_prompt_on_close(self, doc_id: str) -> bool:
        """
        Return True if closing this document should prompt the user.

        A prompt is required when the document exists and has unsaved changes.
        """
        return self.has_unsaved_changes(doc_id)

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

    def _new_untitled_id(self) -> str:
        index = len(self._documents) + 1
        return f"doc-untitled-{index}"
