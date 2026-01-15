from pathlib import Path
from typing import Optional

from textual._node_list import DuplicateIds
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Button, Footer, Select, TextArea, TabbedContent, TabPane, Markdown, \
    DataTable, ContentSwitcher, RichLog

from core.constants import DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE, WELCOME_MESSAGE, WIDTH_SCALES, EXCEPTION_TAB_IDS, \
    SIDE_PANEL_ID_MAPPING
from core.document.context import DocumentContext
from core.theme import CUSTOM_APP_THEMES, APP_THEMES, EDITOR_THEMES
from features.chat.chat_pane import ChatPane
from features.chat.ollama_client import OllamaClient
from features.customizer.customizer_panel import CustomizerPanel
from features.editor.constants import LANGUAGES
from features.editor.editor import Editor
from features.executor import runner
from features.explorer.dialogs import get_dialog_handler
from features.explorer.file_browser import FileBrowser
from ui.top_bar import TopBar
from utils.config_parser import ConfigParser
from utils.editor import register_custom_editor_theme
from utils.keymap import create_mapping_table
from utils.screen import DEFAULT_LEFT_PANEL_WIDTH, get_side_panel_width, get_tabbed_editor_width, \
    DEFAULT_TABBED_EDITOR_WIDTH


class CatnipApp(App):
    """
    Main application entry point responsible for UI orchestration.
    Document state and file lifecycle are delegated to DocumentContext.
    """

    CSS_PATH = "../styles/entry.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("ctrl+s", "save_file", "save", show=False, priority=True),
        Binding("ctrl+shift+c", "open_ai_chat", "cat me", show=False, priority=True),
        Binding("ctrl+shift+s", "save_file_as", "save as", show=False, priority=True),
        Binding("ctrl+w", "close_tab", "close tab", show=False, priority=True),
        Binding("ctrl+1", "show_file_browser",
                "show file browser", show=False),
        Binding("ctrl+2", "show_customizer_panel",
                "show customizer", show=False),
        Binding("ctrl+3", "show_runner_panel", "show runner panel", show=False),
        Binding("ctrl+4", "show_shortcuts",
                "show shortcuts", show=True),
        Binding("ctrl+q", "quit", "quit", show=True),
        Binding("delete", "delete_selected_file", "delete file", show=False),
        Binding("ctrl+o", "open_file", "open file", show=False),
        Binding("ctrl+shift+o", "open_folder", "open folder", show=False),
        Binding("ctrl+shift+right", "extend_side_panel", "extend side-panel", show=True, priority=True),
        Binding("ctrl+shift+left", "reduce_side_panel", "reduce side-panel", show=True, priority=True),
        Binding("ctrl+shift+down", "unhide_top_bar", "unhide top-bar", show=False, priority=True),
        Binding("ctrl+shift+up", "hide_top_bar", "unhide top-bar", show=False, priority=True),
        Binding("ctrl+shift+r", "run_script", "run script", show=False),
        Binding("ctrl+n", "new_file", "new file", show=False),
    ]

    def __init__(self) -> None:
        super().__init__()

        self._init_core_state()
        self._init_config()
        self._init_dialogs()
        self._init_themes()
        self._init_features()

    def _init_core_state(self) -> None:
        self.tabbed_editor = None
        self.documents = DocumentContext()
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self.languages = LANGUAGES
        self.desc_key_pairs = [(b.description, b.key) for b in self.BINDINGS]

    def _init_config(self) -> None:
        self.app_theme = ConfigParser.get("app_theme", "atom_dark")
        self.editor_theme = ConfigParser.get("editor_theme", "atom_dark")

    def _init_dialogs(self) -> None:
        self.dialog_handler = get_dialog_handler()

    def _init_themes(self) -> None:
        for theme in CUSTOM_APP_THEMES:
            self.register_theme(theme)
        self.theme = self.app_theme

    def _init_features(self) -> None:
        self.file_browser = FileBrowser(
            on_open_file=self.open_file_in_tab,
            on_confirm_delete=self.dialog_handler.confirm_action,
        )

        self.customizer_panel = CustomizerPanel(
            APP_THEMES,
            self.app_theme,
            EDITOR_THEMES,
            self.editor_theme,
            self.languages,
        )

        self.runner = RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            id="runner-output",
            auto_scroll=True,
        )

    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        self.tabbed_editor = TabbedContent(
            classes="tabbed-editor", id="tabbed-editor")

        # create a "Welcome" tab with Markdown instructions
        welcome_tab = TabPane(title="Welcome", id="welcome")

        def _mount_welcome_markdown():
            self.tabbed_editor.add_pane(welcome_tab)
            welcome_tab.mount(Markdown(WELCOME_MESSAGE, classes="welcome-md"))

        self.call_after_refresh(_mount_welcome_markdown)

        yield Vertical(
            TopBar(),
            Horizontal(
                Container(
                    Button("📦", id="file-browser",
                           tooltip="Show directory tree panel (Ctrl+1)"),
                    Button("🐳", id="customizer",
                           tooltip="Show customizer panel (Ctrl+2)"),
                    Button("▶️", id="runner",
                           tooltip="Runner (Ctrl+3)"),
                    Button("🧶", id="key-mapping",
                           tooltip="Show key mappings (Ctrl+4)"),
                    Button("🐱", id="cat-me",
                           tooltip="Cat me (Ctrl+Shift+C)"),
                    classes="side-button",
                ),
                ContentSwitcher(
                    self.file_browser,
                    self.customizer_panel,
                    self.runner,
                    id="side-panel",
                    initial="file-browser",
                ),
                self.tabbed_editor,
                classes="main-screen",
            ),
            Footer(),
        )

    def on_mount(self) -> None:
        """
        Add class attribute to File Browser.
        """
        self.query_one(FileBrowser).classes = "file-browser"
        side_panel = self.query_one("#side-panel")
        tabbed_editor = self.query_one(".tabbed-editor")
        side_panel.styles.width = DEFAULT_LEFT_PANEL_WIDTH
        tabbed_editor.styles.width = DEFAULT_TABBED_EDITOR_WIDTH

        config = ConfigParser.load_config()
        if config.get("llm_on_start"):
            OllamaClient.serve()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Handle sidebar button clicks for opening files/folders or switching panels.
        """
        side_panel = self.query_one("#side-panel")
        button_id = event.button.id
        # handle file and folder opening separately
        match event.button.id:
            case "open-file":
                self.open_file_dialog()
                # switch to file browser panel
                side_panel.current = "file-browser"
                # if the side panel is hidden, show it again
                self._enable_side_panel(side_panel)
                return
            case "open-folder":
                self.open_folder_dialog()
                side_panel.current = "file-browser"
                self._enable_side_panel(side_panel)
                return
            case "new-file":
                self.create_a_file()
                side_panel.current = "customizer"
                self._enable_side_panel(side_panel)
                return
            case "key-mapping":
                self.action_show_shortcuts()
                return
            case "cat-me":
                self.action_open_ai_chat()
                return
            case "runner":
                self.action_show_runner_panel()
                return

        if button_id in SIDE_PANEL_ID_MAPPING:
            # switch active panel
            side_panel.current = SIDE_PANEL_ID_MAPPING[button_id]
            self._enable_side_panel(side_panel)
            if side_panel.current == "file-browser":
                # reload file browser
                self.query_one(FileBrowser).reload()

    def _enable_side_panel(self, side_panel: ContentSwitcher) -> None:
        if not side_panel.display:
            side_panel.display = True
            side_panel.styles.width = DEFAULT_LEFT_PANEL_WIDTH
            self.query_one(".tabbed-editor").styles.width = DEFAULT_TABBED_EDITOR_WIDTH
            self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE

    def on_select_changed(self, event: Select.Changed) -> None:
        """
        Handle selection changes in the Customizer Panel.
        """
        select_id = event.select.id
        selected_value = event.value

        try:
            if select_id == "app-theme-picker":
                if selected_value in str(APP_THEMES):
                    self.apply_app_theme(selected_value)
            elif select_id == "editor-theme-picker":
                if selected_value in str(EDITOR_THEMES):
                    self.apply_editor_theme(selected_value)
            elif select_id == "language-picker":
                if selected_value in self.languages:
                    self.apply_language(selected_value)
            else:
                pass
        except TypeError:
            pass

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """
        Mark the active document as dirty when the editor content
        actually diverges from the document's persisted content.

        Note:
        - TextArea.Changed is also fired for programmatic updates
          (e.g. when loading file content).
        - Dirty state is only updated when a real content change occurs.
        """
        tab = event.control.parent

        if not isinstance(tab, TabPane):
            return

        try:
            document = self.documents.get(tab.id)

            # only mark dirty if content actually differs
            if event.control.text != document.content:
                self.documents.mark_dirty(tab.id, event.control.text)
        except KeyError:
            pass

    def action_open_file(self) -> None:
        self.open_file_dialog()

    def action_open_folder(self) -> None:
        self.open_folder_dialog()

    def action_new_file(self) -> None:
        self.create_a_file()

    def action_open_ai_chat(self) -> None:
        """
        Start the LLM, the open or switch to the Cat Me tab.
        """
        OllamaClient.serve()
        tab_id = "cat-me"

        try:
            # create and add the new chat tab
            def get_chat_log() -> RichLog:
                return self.query_one(TabbedContent).query_one("#chat-log")

            chat_tab = ChatPane(get_chat_log=get_chat_log)
            self.tabbed_editor.add_pane(chat_tab)
            self.tabbed_editor.active = tab_id
        except DuplicateIds:
            self.tabbed_editor.active = tab_id

    def action_show_file_browser(self) -> None:
        side_panel = self.query_one("#side-panel")
        side_panel.current = "file-browser"
        self._enable_side_panel(side_panel)

    def action_show_customizer_panel(self) -> None:
        side_panel = self.query_one("#side-panel")
        side_panel.current = "customizer"
        self._enable_side_panel(side_panel)

    def action_show_runner_panel(self) -> None:
        side_panel = self.query_one("#side-panel")
        side_panel.current = "runner-output"
        self._enable_side_panel(side_panel)
        runner_output = self.query_one("#side-panel").query_one("#runner-output", expect_type=RichLog)
        if not runner_output.lines:
            output = "➜ ✗ (catnip):"
            runner_output.write(output)

    def action_show_shortcuts(self) -> None:
        """
        Open the key mappings inside a new tab in the tabbed editor.
        """
        tab_id = "key-mappings"
        try:
            # create a new tab for key mappings
            tab = TabPane(title="Shortcuts", id=tab_id)

            # create a DataTable for key mappings
            table = DataTable(id="key-mapping-table")
            table.add_columns("Action", "Shortcut")
            table = create_mapping_table(table, self.desc_key_pairs, app.get_css_variables()["accent"])

            def mount_table():
                """Mount the table inside the tab."""
                tab.mount(VerticalScroll(table))

            # add tab and mount content
            self.tabbed_editor.add_pane(tab)
            self.call_after_refresh(mount_table)

            self.tabbed_editor.active = tab_id
        except DuplicateIds:
            self.tabbed_editor.active = tab_id

    def action_extend_side_panel(self) -> None:
        """
        Extend the width of the side panel.
        """
        self._adjust_side_panel(is_reduce=False)

    def action_reduce_side_panel(self) -> None:
        """
        Reduce the width of the side panel.
        """
        self._adjust_side_panel()

    def _adjust_side_panel(self, is_reduce: bool = True) -> None:
        """
        Adjust the width of the left side panel.
        """
        side_panel = self.query_one("#side-panel")

        # get the current width scale index
        index = WIDTH_SCALES.index(self.side_panel_width_percentage)

        # skip adjustment if already at boundary
        boundary_value = min(WIDTH_SCALES) if is_reduce else max(WIDTH_SCALES)
        if self.side_panel_width_percentage != boundary_value:
            tabbed_editor = self.query_one(".tabbed-editor")

            # calculate the next index based on the direction
            next_index = index - 1 if is_reduce else index + 1
            self.side_panel_width_percentage = WIDTH_SCALES[next_index]

            # hide the panel if reduced to minimum, otherwise show it
            side_panel.display = self.side_panel_width_percentage != min(WIDTH_SCALES)

            # apply the new widths to side panel and the editor
            side_panel_width = get_side_panel_width(self.side_panel_width_percentage)
            side_panel.styles.width = side_panel_width
            tabbed_editor.styles.width = get_tabbed_editor_width(side_panel_width)

    def action_hide_top_bar(self) -> None:
        """
        Hide the Top Bar.
        """
        main_screen = self.query_one(".main-screen")
        top_bar = self.query_one(".top-bar")

        if top_bar.display:
            top_bar.display = False
            main_screen.add_class("expanded")

    def action_unhide_top_bar(self) -> None:
        """
        Unhide the Top Bar.
        """
        main_screen = self.query_one(".main-screen")
        top_bar = self.query_one(".top-bar")

        if not top_bar.display:
            top_bar.display = True
            main_screen.remove_class("expanded")

    def action_delete_selected_file(self) -> None:
        """
        Delete the selected file or folder and close any open document
        associated with it.
        """
        deleted_path = self.query_one(FileBrowser).delete_selected_item()
        if not deleted_path:
            return

        closed_docs = self.documents.close_by_path(deleted_path)
        for doc_id in closed_docs:
            self.tabbed_editor.remove_pane(doc_id)

        # send notify and refresh file browser
        self.notify(f"Deleted {str(deleted_path)}")
        self.query_one(FileBrowser).reload()

    def action_save_file(self) -> None:
        """
        Save the currently active document.

        If the active tab represents a document managed by DocumentContext,
        the document is saved to disk. If the document has not been saved
        before, the user is prompted to choose a save location.

        Non-document tabs (e.g. welcome screen, shortcuts, AI chat) are ignored.
        """
        tab = self.tabbed_editor.active_pane
        if not tab:
            return

        try:
            document = self.documents.get(tab.id)
        except KeyError:
            return

        # if the document has never been saved, ask for a path
        if document.path is None:
            file_path = self.dialog_handler.select_folder_save()
            if not file_path:
                return
            try:
                document_id = document.id
                self.documents.save_as(document_id, file_path)
                self.notify(f"File saved to {file_path}")

                # open the saved file in new tab
                self.open_file_in_tab(file_path)

                # remove old tab
                self.tabbed_editor.remove_pane(document_id)

                # open the file browser
                side_panel = self.query_one("#side-panel")
                side_panel.current = "file-browser"

                # refresh file browser after saving a new file
                self.query_one(FileBrowser).path = str(file_path.parent)
                self.query_one(FileBrowser).reload()

            except Exception as e:
                print(f"Failed to save file: {str(e)}")

        elif self.documents.get(document.id).dirty:
            try:
                self.documents.save(document.id)
                self.query_one(FileBrowser).reload()
                self.notify(f"Saved {document.title}")
            except Exception as e:
                self.notify(f"Failed to save file: {e}", severity="error")
                return

    def action_save_file_as(self) -> None:
        """
        Save the currently active document under a new file path.

        If the active tab represents a document managed by DocumentContext,
        the user is prompted to choose a new save location. The document is
        then persisted to disk and its identity (path, title, dirty state)
        is updated accordingly.

        Non-document tabs are ignored.
        """
        tab = self.tabbed_editor.active_pane
        if not tab:
            return

        try:
            document = self.documents.get(tab.id)
        except KeyError:
            return

        new_file_path = self.dialog_handler.select_folder_save()
        if not new_file_path:
            return

        try:
            self.documents.save_as(document.id, new_file_path)
            tab.title = Path(new_file_path).name

            # refresh file browser after saving a new file
            self.query_one(FileBrowser).path = str(new_file_path.parent)
            self.query_one(FileBrowser).reload()

            self.notify(f"Saved as {new_file_path}")
        except Exception as e:
            self.notify(f"Failed to save file: {e}", severity="error")

    def action_close_tab(self) -> None:
        """
        Close the currently active tab.

        If the active tab corresponds to a document managed by DocumentContext and
        the document has unsaved changes, the user is prompted to save before the
        tab is closed.

        Tabs that do not represent documents (e.g. welcome screen, key mappings,
        AI chat) are closed immediately without any save prompt.
        """
        tab = self.tabbed_editor.active_pane
        if not tab:
            return

        try:
            document = self.documents.get(tab.id)
            if document.dirty:
                confirm = self.dialog_handler.confirm_action(
                    title="Unsaved Changes",
                    message=f"Do you want to save changes to {document.title}?"
                )
                if confirm:
                    if document.path is None:
                        file_path = self.dialog_handler.select_folder_save()
                        if not file_path:
                            return
                    else:
                        self.documents.save(document.id)

            self.documents.close(document.id)
        except KeyError:
            pass
        finally:
            self.tabbed_editor.remove_pane(tab.id)

    def action_quit(self) -> None:
        """
        Quit the application, prompting to save unsaved document changes if needed.

        This method iterates over all open tabs and checks whether each tab represents
        a document managed by DocumentContext. For document tabs with unsaved changes,
        the user is prompted to confirm saving before the application exits.

        Non-document tabs (e.g. welcome screen, key mappings, AI chat) are ignored.
        """
        # Iterate over open panes in reverse order (last active first)
        for tab in reversed(list(self.tabbed_editor.query(TabPane))):
            try:
                document = self.documents.get(tab.id)
            except KeyError:
                continue

            if document.dirty:
                self.tabbed_editor.active = tab.id
                confirm = self.dialog_handler.confirm_action(
                    title="Unsaved Changes",
                    message=f"Do you want to save changes to {document.title}?",
                )
                if confirm:
                    self.documents.save(document.id)

        self.exit()

    def action_run_script(self) -> None:
        """
        Run the currently active document using the configured runner.

        The active tab must represent a runnable document managed by
        DocumentContext. The document is saved if needed, the runner panel
        is shown, and the execution output is written to the runner log.

        Non-document tabs or empty documents are ignored.
        """
        file_path = self._get_runnable_file()
        if not file_path:
            return

        runner_output = self._prepare_runner_ui()
        output = runner.run_file(file_path)
        runner_output.write(f"{output}\n➜ ✗ (catnip):")

    def _get_runnable_file(self) -> Optional[Path]:
        active_tab = self.tabbed_editor.active_pane

        if not active_tab or active_tab.id in EXCEPTION_TAB_IDS:
            return None

        text_area = active_tab.query_one(TextArea)
        if not text_area.text.strip():
            return None

        return self.documents.get(active_tab.id).path

    def _prepare_runner_ui(self) -> RichLog:
        self.action_save_file()
        self.action_show_runner_panel()
        return self.query_one("#side-panel").query_one("#runner-output", expect_type=RichLog)

    def apply_app_theme(self, app_theme: str) -> None:
        """
        Apply and save the selected app-wide theme.
        """
        ConfigParser.update_config_file("app_theme", app_theme)
        self.theme = app_theme

        try:
            mappings_tab = self.tabbed_editor.get_pane("key-mappings")
            mappings_table = self.query_one("#key-mapping-table", expect_type=DataTable)
            mappings_table.clear()
            create_mapping_table(mappings_table, self.desc_key_pairs, app.get_css_variables()["accent"])
            mappings_tab.refresh()
        except Exception:
            pass

    def apply_editor_theme(self, theme: str) -> None:
        """
        Apply the selected theme to the code editor (syntax highlighting).
        """

        for tab in self.tabbed_editor.query(TabPane):
            if tab.query(TextArea):
                text_area = tab.query_one(TextArea)
                register_custom_editor_theme(text_area)
                text_area.theme = theme

        # save theme to project config and editor_theme attr
        ConfigParser.update_config_file("editor_theme", theme)
        self.editor_theme = theme

    def apply_language(self, language: str) -> None:
        """
        Apply the selected language for syntax highlighting.
        """
        active_tab = self.tabbed_editor.active_pane
        if active_tab and active_tab.id not in EXCEPTION_TAB_IDS:
            text_area = active_tab.query_one(TextArea)
            text_area.language = Editor.normalize_language(language)

    def open_file_dialog(self) -> None:
        """
        Open a file selection dialog and open the selected files in editor tabs.
        """
        file_paths = self.dialog_handler.select_file()
        if not file_paths:
            return

        for file in file_paths:
            self.open_file_in_tab(file)

        file_browser = self.query_one(FileBrowser)
        file_browser.path = str(file_paths[0].parent)

    def open_folder_dialog(self) -> None:
        """
        Open a folder selection dialog and load it into the file browser.
        """
        folder_path = self.dialog_handler.select_folder()
        if not folder_path:
            return

        file_browser = self.query_one(FileBrowser)
        file_browser.path = str(Path(folder_path).resolve())
        file_browser.reload()

    def open_file_in_tab(self, file_path: Path) -> None:
        """
        Open a file in the editor as a tab.

        This method delegates document loading and lifecycle management to
        DocumentContext. If the file is already open, the existing tab is
        activated. Otherwise, a new editor tab is created and populated
        with the file content.
        """
        file_path = file_path.resolve()

        try:
            document = self.documents.open(file_path)
        except Exception as e:
            self.notify(f"Failed to open file: {e}", severity="error")
            return

        try:
            tab = TabPane(
                id=document.id,
                title=document.title,
                name=document.title,
            )

            self.tabbed_editor.add_pane(tab)
            self.call_after_refresh(
                lambda: self._mount_editor_for_document(tab, document)
            )
            self.tabbed_editor.active = document.id
        except DuplicateIds:
            # if tab already exists → just activate
            self.tabbed_editor.active = document.id

    def create_a_file(self) -> None:
        """
        Create a new untitled document and open it in the editor.

        This method delegates untitled document creation to DocumentContext,
        then creates a corresponding editor tab and mounts a text editor
        initialized with the document's default state.
        """

        try:
            document = self.documents.create_untitled()
        except Exception as e:
            self.notify(f"Failed to create new file: {e}", severity="error")
            return

        tab = TabPane(
            id=document.id,
            title=document.title,
            name=document.title,
        )

        self.tabbed_editor.add_pane(tab)
        self.call_after_refresh(
            lambda: self._mount_editor_for_document(tab, document)
        )
        self.tabbed_editor.active = document.id

    def _mount_editor_for_document(self, tab: TabPane, document) -> None:
        text_area = Editor.code_editor(
            language=document.language or "markdown",
            soft_wrap=True,
        )
        register_custom_editor_theme(text_area)
        text_area.theme = self.editor_theme
        text_area.load_text(document.content or "")

        tab.mount(text_area)


if __name__ == "__main__":
    app = CatnipApp()
    app.run()
