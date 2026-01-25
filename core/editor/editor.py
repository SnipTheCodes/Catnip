from __future__ import annotations

from textual import events, on
from textual.widgets import TextArea

from .controller import EditorController


class Editor(TextArea):
    """A subclass of TextArea with AI-powered autocomplete using Together AI."""

    def __init__(self, document_id: str, controller: EditorController, *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.document_id = document_id
        self.controller = controller

    def on_key(self, event: events.Key) -> None:
        """Handles special character insertions."""

        if event.character in ["(", "{", "[", "'", '"']:
            pairs = {"(": "()", "{": "{}", "[": "[]", "'": "''", '"': '""'}
            self.insert(pairs[event.character])
            self.move_cursor_relative(columns=-1)
            event.prevent_default()

    @on(TextArea.Changed)
    def on_changed(self, event: TextArea.Changed) -> None:
        """Notify the controller when the editor content changes."""

        self.controller.on_editor_text_changed(self.document_id,
                                               event.control.text, )

    @on(TextArea.SelectionChanged)
    def handle_selection_change(self, event: TextArea.SelectionChanged):
        """Copy selected text to clipboard when a selection is made."""

        if not event.selection.is_empty:
            self.action_copy()

    @classmethod
    def for_document(cls, *, document_id: str, controller: EditorController,
                     language: str = "markdown", **kwargs, ) -> Editor:
        """Create an Editor instance configured for a specific document."""

        return cls(document_id=document_id, controller=controller,
                   language=language, show_line_numbers=True, **kwargs)

    @staticmethod
    def normalize_language(language: str) -> str:
        """Normalize language names to match supported editor syntax."""

        return "javascript" if language == "typescript" else language
