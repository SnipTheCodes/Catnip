from pathlib import Path
from typing import Optional

from textual._node_list import DuplicateIds
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, TextArea, TabbedContent, TabPane, Markdown, \
    ContentSwitcher, RichLog
from core.document.context import DocumentContext
from core.tab.constants import EXCEPTION_TAB_IDS
from core.tab.lifecycle import TabLifecycle
from core.theme import APP_THEMES, EDITOR_THEMES, CUSTOM_APP_THEMES
from features.chat.chat_pane import ChatPane
from features.chat.ollama_client import OllamaClient
from features.customizer.customizer_controller import CustomizerController
from features.customizer.customizer_panel import CustomizerPanel
from features.editor.controller import EditorController
from features.editor.editor import Editor
from features.editor.languages import supported_languages
from features.executor import runner
from features.explorer.dialogs import get_dialog_handler
from features.explorer.file_browser import FileBrowser
from features.shortcuts.shortcuts_tab import ShortcutsTab
from ui.constants import DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE, WELCOME_MESSAGE
from ui.layout.layout_controller import LayoutController
from ui.sidebar.sidebar import SideBar
from ui.topbar.top_bar import TopBar
from utils.config_parser import ConfigParser
from utils.editor import register_custom_editor_theme
from utils.screen import DEFAULT_LEFT_PANEL_WIDTH, DEFAULT_TABBED_EDITOR_WIDTH


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

        self._init_config()
        self._init_core_state()
        self._init_dialogs()
        self._init_themes()
        self._init_features()
        self._init_layout()

    def _init_core_state(self) -> None:
        self.tabbed_editor = None
        self.documents = DocumentContext()
        self.tab_lifecycle = TabLifecycle(self.documents)
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self.languages = supported_languages()
        self.desc_key_pairs = [(b.description, b.key) for b in self.BINDINGS]

    def _init_config(self) -> None:
        self.app_theme = ConfigParser.get("app_theme", "dracula")
        self.editor_theme = ConfigParser.get("editor_theme", "dracula")

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

        self.editor_controller = EditorController(self.documents)
        self.customizer_controller = CustomizerController(self.app)
        self.customizer_panel = CustomizerPanel(
            APP_THEMES,
            self.app_theme,
            EDITOR_THEMES,
            self.editor_theme,
            self.languages,
            self.customizer_controller
        )

        self.runner = RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            id="runner-output",
            auto_scroll=True,
        )

    def _init_layout(self):
        self.layout_controller = LayoutController(self.app)

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
                SideBar(),
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
        match event.button.id:
            case "open-file":
                self.open_file_dialog()

            case "open-folder":
                self.open_folder_dialog()

            case "new-file":
                self.create_a_file()

            case "file-browser":
                self.layout_controller.show_side_panel("file-browser")

            case "customizer":
                self.layout_controller.show_side_panel("customizer")

            case "runner":
                self.layout_controller.show_side_panel("runner-output")

            case "key-mapping":
                self.action_show_shortcuts()

            case "cat-me":
                self.action_open_ai_chat()

            case _:
                return

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

        # create and add the new chat tab
        def get_chat_log() -> RichLog:
            return self.query_one(TabbedContent).query_one("#chat-log")

        tab = ChatPane(get_chat_log=get_chat_log)
        self._open_or_focus_tab(tab)

    def action_show_file_browser(self) -> None:
        self.layout_controller.show_side_panel("file-browser")

    def action_show_customizer_panel(self) -> None:
        self.layout_controller.show_side_panel("customizer")

    def action_show_runner_panel(self) -> None:
        self.layout_controller.show_side_panel("runner-output")
        runner_output = self.query_one("#side-panel").query_one("#runner-output", expect_type=RichLog)
        if not runner_output.lines:
            output = "➜ ✗ (catnip):"
            runner_output.write(output)

    def action_show_shortcuts(self) -> None:
        """
        Open the key mappings inside a new tab in the tabbed editor.
        """
        tab = ShortcutsTab(
            self.desc_key_pairs,
            app.get_css_variables()["accent"],
        )
        self._open_or_focus_tab(tab)

    def action_extend_side_panel(self) -> None:
        """
        Extend the width of the side panel.
        """
        self.layout_controller.adjust_side_panel(reduce=False)

    def action_reduce_side_panel(self) -> None:
        """
        Reduce the width of the side panel.
        """
        self.layout_controller.adjust_side_panel()

    def action_hide_top_bar(self) -> None:
        """
        Hide the Top Bar.
        """
        self.layout_controller.hide_top_bar()

    def action_unhide_top_bar(self) -> None:
        """
        Unhide the Top Bar.
        """
        self.layout_controller.show_top_bar()

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

        document = self.documents.try_get(tab.id)

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
                self._refresh_file_browser(file_path)

            except Exception as e:
                print(f"Failed to save file: {str(e)}")

        elif self.documents.has_unsaved_changes(document.id):
            try:
                self.documents.save(document.id)
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

        document = self.documents.try_get(tab.id)

        new_file_path = self.dialog_handler.select_folder_save()
        if not new_file_path:
            return

        try:
            self.documents.save_as(document.id, new_file_path)
            tab.title = Path(new_file_path).name

            # refresh file browser after saving a new file
            self._refresh_file_browser(new_file_path)

            self.notify(f"Saved as {new_file_path}")
        except Exception as e:
            self.notify(f"Failed to save file: {e}", severity="error")

    def _refresh_file_browser(self, path: Path) -> None:
        browser = self.query_one(FileBrowser)
        browser.path = str(path.parent)
        browser.reload()

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

        if self.tab_lifecycle.needs_save_prompt(tab.id):
            name = self.tab_lifecycle.get_display_name(tab.id)

            confirm = self.dialog_handler.confirm_action(
                title="Unsaved Changes",
                message=f"Do you want to save changes to {name}?"
            )

            if confirm and not self._prompt_and_save_document(self.documents.get(tab.id)):
                return

        self.tab_lifecycle.on_tab_closed(tab.id)
        self.tabbed_editor.remove_pane(tab.id)
        self.query_one(FileBrowser).reload()

    def action_quit(self) -> None:
        """
        Quit the application, prompting to save unsaved document changes if needed.

        This method iterates over all open tabs and checks whether each tab represents
        a document managed by DocumentContext. For document tabs with unsaved changes,
        the user is prompted to confirm saving before the application exits.

        Non-document tabs (e.g. welcome screen, key mappings, AI chat) are ignored.
        """
        # iterate over open panes in reverse order (last active first)
        for tab in reversed(list(self.tabbed_editor.query(TabPane))):
            if self.tab_lifecycle.needs_save_prompt(tab.id):
                name = self.tab_lifecycle.get_display_name(tab.id)
                self.tabbed_editor.active = tab.id

                confirm = self.dialog_handler.confirm_action(
                    title="Unsaved Changes",
                    message=f"Do you want to save changes to {name}?"
                )
                if confirm and not self._prompt_and_save_document(self.documents.get(tab.id)):
                    return
            self.tab_lifecycle.on_tab_closed(tab.id)

        self.exit()

    def _prompt_and_save_document(self, document) -> bool:
        """
        Prompt the user to save changes for the given document.

        Returns True if the document was saved successfully.
        Returns False if the user cancelled the save flow.
        """
        if document.path is None:
            file_path = self.dialog_handler.select_folder_save()
            if not file_path:
                return False

            self.documents.save_as(document.id, file_path)
            self.notify(f"File saved to {file_path}")

            return True

        self.documents.save(document.id)
        self.notify(f"File saved!")

        return True

    def action_run_script(self) -> None:
        """
        Run the currently active document using a temp file.

        The document is NOT auto-saved. Unsaved changes are written to a
        temporary file under ~/.catnip/tmp and executed from there.
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

        if not self.documents.is_document(active_tab.id):
            return None

        document = self.documents.get(active_tab.id)

        if not document.content.strip():
            return None

        # write and run temp file instead of forcing save
        return self.documents.write_temp(document.id)

    def _prepare_runner_ui(self) -> RichLog:
        self.action_show_runner_panel()
        return self.query_one("#side-panel").query_one("#runner-output", expect_type=RichLog)

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
        self.layout_controller.show_side_panel("file-browser")

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
        self.layout_controller.show_side_panel("file-browser")

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

        tab = TabPane(
            id=document.id,
            title=document.title,
            name=document.title,
        )
        self._open_or_focus_tab(tab, document)

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
            title=document.title
        )

        self.tabbed_editor.add_pane(tab)
        self.call_after_refresh(
            lambda: self._mount_editor_for_document(tab, document)
        )
        self.tabbed_editor.active = document.id

    def _mount_editor_for_document(self, tab: TabPane, document) -> None:
        text_area = Editor.for_document(
            document_id=document.id,
            controller=self.editor_controller,
            language=document.language or "markdown",
            soft_wrap=True,
        )
        register_custom_editor_theme(text_area)
        text_area.theme = self.editor_theme
        text_area.load_text(document.content or "")

        tab.mount(text_area)

    def _open_or_focus_tab(self, tab: TabPane, document: DocumentContext = None):
        try:
            self.tabbed_editor.add_pane(tab)
            if document is not None:
                self.call_after_refresh(
                    lambda: self._mount_editor_for_document(tab, document)
                )
        except DuplicateIds:
            pass
        self.tabbed_editor.active = tab.id


if __name__ == "__main__":
    app = CatnipApp()
    app.run()
