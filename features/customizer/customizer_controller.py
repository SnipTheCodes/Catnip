from textual.widgets import TextArea, TabPane, DataTable

from config.app import AppConfig
from core.tab.constants import EXCEPTION_TAB_IDS
from core.theme import APP_THEMES, EDITOR_THEMES
from core.editor.editor import Editor
from core.editor.languages import supported_languages
from utils.editor import register_custom_editor_theme
from utils.keymap import create_mapping_table


class CustomizerController:
    def __init__(self, app: "CatnipApp"):
        self.app = app
        self.config = AppConfig.load()

    def handle_select_change(self, select_id: str, value: str) -> None:
        """  
        Handle selection changes in the Customizer Panel.
        """
        if select_id == "app-theme-picker":
            if value in str(APP_THEMES):
                self.apply_app_theme(value)

        elif select_id == "editor-theme-picker":
            if value in str(EDITOR_THEMES):
                self.apply_editor_theme(value)

        elif select_id == "language-picker":
            if value in supported_languages():
                self.apply_language(value)

    def apply_app_theme(self, app_theme: str) -> None:
        """
        Apply and save the selected app-wide theme.
        """
        self.app.theme = app_theme
        self.config.app_theme = app_theme
        self.config.save()

        try:
            mappings_tab = self.app.tabbed_editor.get_pane("key-mappings")
            mappings_table = self.app.query_one("#key-mapping-table",
                                                expect_type=DataTable)
            mappings_table.clear()
            create_mapping_table(mappings_table, self.app.desc_key_pairs,
                                 self.app.get_css_variables()["accent"])
            mappings_tab.refresh()
        except Exception:
            pass

    def apply_editor_theme(self, theme: str) -> None:
        """
        Apply the selected theme to the code editor (syntax highlighting).
        """
        for tab in self.app.tabbed_editor.query(TabPane):
            if tab.query(TextArea):
                text_area = tab.query_one(TextArea)
                register_custom_editor_theme(text_area)
                text_area.theme = theme

        # save theme to project config and editor_theme attr
        self.app.editor_theme = theme
        self.config.editor_theme = theme
        self.config.save()

    def apply_language(self, language: str) -> None:
        """  
        Apply the selected language for syntax highlighting.
        """
        active_tab = self.app.tabbed_editor.active_pane
        if active_tab and active_tab.id not in EXCEPTION_TAB_IDS:
            text_area = active_tab.query_one(TextArea)
            text_area.language = Editor.normalize_language(language)
