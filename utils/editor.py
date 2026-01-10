from textual.widgets import TextArea

from core.theme import CUSTOM_EDITOR_THEMES


def register_custom_editor_theme(text_area: TextArea) -> None:
    for theme in CUSTOM_EDITOR_THEMES:
        text_area.register_theme(theme)
