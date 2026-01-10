from pathlib import Path

from pygments.lexers import get_lexer_for_filename
from textual import events, on
from textual.widgets import TextArea


class Editor(TextArea):
    """A subclass of TextArea with AI-powered autocomplete using Together AI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.suggestion = ""

    def _on_key(self, event: events.Key) -> None:
        """Handles special character insertions and cancels ongoing AI requests if needed."""
        if event.character in ["(", "{", "[", "'", '"']:
            pairs = {"(": "()", "{": "{}", "[": "[]", "'": "''", '"': '""'}
            self.insert(pairs[event.character])
            self.move_cursor_relative(columns=-1)
            event.prevent_default()

    @on(TextArea.SelectionChanged)
    def handle_selection_change(self, event: TextArea.SelectionChanged):
        if not event.selection.is_empty:
            self.action_copy()

    @staticmethod
    def get_file_language(file_path: Path, languages) -> str:
        """Returns the programming language based on the file extension."""
        file_extension = file_path.suffix.lower()
        lexer = get_lexer_for_filename(file_extension)
        language = lexer.__class__.__name__.replace("Lexer", "").lower()
        if language == 'typescript':
            return 'javascript'
        else:
            return language if language in languages else "markdown"

    @staticmethod
    def normalize_language(language: str) -> str:
        return "javascript" if language == "typescript" else language
