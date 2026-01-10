from textual.containers import Container
from textual.widgets import Select


class CustomizerPanel(Container):
    """A slide-in customization panel for selecting color scheme, theme, and language."""

    def __init__(self, app_themes: list, current_app_theme: str, editor_themes: list, current_editor_theme: str,
                 languages: list):
        super().__init__(id="customizer")
        self.app_themes = app_themes
        self.current_app_theme = current_app_theme
        self.editor_themes = editor_themes
        self.current_editor_theme = current_editor_theme
        self.languages = languages

        # remove duplicates from language options
        unique_languages = sorted(set(languages))
        self.languages = [(lang.capitalize(), lang)
                          for lang in unique_languages]

    def compose(self):
        """Create the customization panel layout."""
        yield Container(
            Select(
                options=self.app_themes,
                value=self.current_app_theme,
                prompt="Select an app theme",
                tooltip="Select a theme to apply to the app",
                id="app-theme-picker",
            ),
            Select(
                options=self.editor_themes,
                value=self.current_editor_theme,
                prompt="Select an editor theme",
                tooltip="Select a theme to apply to the editor",
                id="editor-theme-picker",
            ),
            Select(
                options=self.languages,
                value="python",
                prompt="Select a language",
                tooltip="Select a programming language for the active tab",
                id="language-picker",
            ),
        )
