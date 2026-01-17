from textual import events, on
from textual.widgets import TextArea

from features.editor.controller import EditorController


class Editor(TextArea):
    """A subclass of TextArea with AI-powered autocomplete using Together AI."""

    def __init__(
            self,
            document_id: str,
            controller: EditorController,
            *args,
            **kwargs):
        super().__init__(*args, **kwargs)
        self.document_id = document_id
        self.controller = controller

    def _on_key(self, event: events.Key) -> None:
        """Handles special character insertions and cancels ongoing AI requests if needed."""
        if event.character in ["(", "{", "[", "'", '"']:
            pairs = {"(": "()", "{": "{}", "[": "[]", "'": "''", '"': '""'}
            self.insert(pairs[event.character])
            self.move_cursor_relative(columns=-1)
            event.prevent_default()

    @on(TextArea.Changed)
    def on_changed(self, event: TextArea.Changed) -> None:
        self.controller.on_editor_text_changed(
            self.document_id,
            event.control.text,
        )

    @on(TextArea.SelectionChanged)
    def handle_selection_change(self, event: TextArea.SelectionChanged):
        if not event.selection.is_empty:
            self.action_copy()

    @classmethod
    def for_document(
            cls,
            *,
            document_id: str,
            controller: EditorController,
            language: str = "markdown",
            **kwargs,
    ) -> "Editor":
        editor = cls(
            document_id=document_id,
            controller=controller,
            language=language,
            **kwargs,
        )
        return editor

    @staticmethod
    def normalize_language(language: str) -> str:
        return "javascript" if language == "typescript" else language
