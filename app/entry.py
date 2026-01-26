from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Footer, TabbedContent, TabPane, Markdown, \
    ContentSwitcher, RichLog

from app.workflows.file_workflow import FileWorkflow
from config.app import AppConfig
from core.document.context import DocumentContext
from core.document.document import Document
from core.editor.controller import EditorController
from core.editor.editor import Editor
from core.editor.languages import supported_languages
from core.explorer.dialogs import get_dialog_handler
from core.explorer.file_browser import FileBrowser
from core.tab.constants import WELCOME_TAB_ID
from core.tab.lifecycle import TabLifecycle
from core.theme import APP_THEMES, EDITOR_THEMES, CUSTOM_APP_THEMES
from features.chat.chat_pane import ChatPane
from features.chat.ollama_client import OllamaClient
from features.customizer.customizer_controller import CustomizerController
from features.customizer.customizer_panel import CustomizerPanel
from features.executor import runner
from features.shortcuts.shortcuts_tab import ShortcutsTab
from ui.constants import DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE, WELCOME_MESSAGE
from ui.layout.layout_controller import LayoutController, SidePanelId
from ui.sidebar.sidebar import SideBar
from ui.topbar.top_bar import TopBar
from utils.editor import register_custom_editor_theme, get_runnable_file
from utils.screen import DEFAULT_LEFT_PANEL_WIDTH, DEFAULT_TABBED_EDITOR_WIDTH
from utils.tabs import is_open


class CatnipApp(App):
    """
    Main application entry point responsible for UI orchestration.
    Document state and file lifecycle are delegated to DocumentContext.
    """

    CSS_PATH = "../styles/entry.tcss"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("ctrl+s", "save_file", "save", show=False, priority=True),
        Binding("ctrl+shift+c", "open_ai_chat", "cat me", show=False,
                priority=True),
        Binding("ctrl+shift+s", "save_file_as", "save as", show=False,
                priority=True),
        Binding("ctrl+w", "close_tab", "close tab", show=False, priority=True),
        Binding("ctrl+1", "show_file_browser", "show file browser", show=False),
        Binding("ctrl+2", "show_customizer_panel", "show customizer",
                show=False),
        Binding("ctrl+3", "show_runner_panel", "show runner panel", show=False),
        Binding("ctrl+4", "show_shortcuts", "show shortcuts", show=True),
        Binding("ctrl+q", "quit", "quit", show=True),
        Binding("delete", "delete_selected_file", "delete file", show=False),
        Binding("ctrl+o", "open_file", "open file", show=False),
        Binding("ctrl+shift+o", "open_folder", "open folder", show=False),
        Binding("ctrl+shift+right", "extend_side_panel", "extend side-panel",
                show=True, priority=True),
        Binding("ctrl+shift+left", "reduce_side_panel", "reduce side-panel",
                show=True, priority=True),
        Binding("ctrl+shift+down", "unhide_top_bar", "unhide top-bar",
                show=False, priority=True),
        Binding("ctrl+shift+up", "hide_top_bar", "unhide top-bar", show=False,
                priority=True),
        Binding("ctrl+shift+r", "run_script", "run script", show=False),
        Binding("ctrl+n", "new_file", "new file", show=False), ]

    def __init__(self) -> None:
        super().__init__()

        self.tabbed_editor = None

        self._init_config()
        self._init_core_state()
        self._init_dialogs()
        self._init_themes()
        self._init_features()
        self._init_layout()

    def _init_core_state(self) -> None:
        self.documents = DocumentContext()
        self.tab_lifecycle = TabLifecycle(self.documents)
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self.languages = supported_languages()
        self.desc_key_pairs = [(b.description, b.key) for b in self.BINDINGS]

    def _init_config(self) -> None:
        self.config = AppConfig.load()
        self.app_theme = self.config.app_theme
        self.editor_theme = self.config.editor_theme

    def _init_dialogs(self) -> None:
        self.dialog_handler = get_dialog_handler()

    def _init_themes(self) -> None:
        for theme in CUSTOM_APP_THEMES:
            self.register_theme(theme)
        self.theme = self.app_theme

    def _init_features(self) -> None:
        self.editor_controller = EditorController(self.documents)
        self.customizer_controller = CustomizerController(self.app)

        self.file_browser = FileBrowser(on_open_file=self.open_file_in_tab,
                                        on_confirm_delete=self.dialog_handler.confirm_action, )

        self.customizer_panel = CustomizerPanel(APP_THEMES, self.app_theme,
                                                EDITOR_THEMES,
                                                self.editor_theme,
                                                self.languages,
                                                self.customizer_controller)

        self.runner = RichLog(highlight=True, markup=True, wrap=True,
                              id="runner-output", auto_scroll=True, )

        self.file_workflow = FileWorkflow(documents=self.documents,
                                          dialogs=self.dialog_handler,
                                          notify=self.notify)

    def _init_layout(self):
        self.layout_controller = LayoutController(self.app)

    def compose(self) -> ComposeResult:
        """Create the screen layout."""

        self.tabbed_editor = TabbedContent(classes="tabbed-editor",
                                           id="tabbed-editor")

        yield Vertical(TopBar(), Horizontal(SideBar(),
                                            ContentSwitcher(self.file_browser,
                                                            self.customizer_panel,
                                                            self.runner,
                                                            id="side-panel",
                                                            initial="file-browser", ),
                                            self.tabbed_editor,
                                            classes="main-screen", ),
                       Footer(), )

    def on_mount(self) -> None:
        """Mount Welcome tab, set main component's width, and start LLM, if applicable."""

        welcome_tab = TabPane(title="Welcome", id=WELCOME_TAB_ID)
        self.tabbed_editor.add_pane(welcome_tab)
        welcome_tab.mount(Markdown(WELCOME_MESSAGE))

        self.query_one("#side-panel").styles.width = DEFAULT_LEFT_PANEL_WIDTH
        self.query_one(TabbedContent).styles.width = DEFAULT_TABBED_EDITOR_WIDTH

        if self.config.llm_on_start:
            OllamaClient.serve()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks for opening files/folders or switching panels."""

        match event.button.id:
            case "open-file":
                self.open_file_dialog()

            case "open-folder":
                self.open_folder_dialog()

            case "new-file":
                self.create_a_file()

            case "file-browser":
                self.layout_controller.show_side_panel(SidePanelId.FILE_BROWSER)

            case "customizer":
                self.layout_controller.show_side_panel(SidePanelId.CUSTOMIZER)

            case "runner":
                self.layout_controller.show_side_panel(
                    SidePanelId.RUNNER_OUTPUT)

            case "key-mapping":
                self.action_show_shortcuts()

            case "cat-me":
                self.action_open_ai_chat()

            case _:
                return

    def action_open_file(self) -> None:
        self.open_file_dialog()

    def action_open_folder(self) -> None:
        self.open_folder_dialog()

    def action_new_file(self) -> None:
        self.create_a_file()

    def action_show_file_browser(self) -> None:
        self.layout_controller.show_side_panel(SidePanelId.FILE_BROWSER)

    def action_show_customizer_panel(self) -> None:
        self.layout_controller.show_side_panel(SidePanelId.CUSTOMIZER)

    def action_show_runner_panel(self) -> None:
        self.layout_controller.show_side_panel(SidePanelId.RUNNER_OUTPUT)
        runner_output = self.query_one("#runner-output", expect_type=RichLog)
        if not runner_output.lines:
            output = "➜ ✗ (catnip):"
            runner_output.write(output)

    def action_show_shortcuts(self) -> None:
        """Open the key mappings inside a new tab in the tabbed editor."""

        tab = ShortcutsTab(self.desc_key_pairs,
                           app.get_css_variables()["accent"], )
        self._open_or_focus_tab(tab)

    def action_open_ai_chat(self) -> None:
        """Start the LLM, then create/switch to the Cat Me tab."""

        OllamaClient.serve()

        # create and add the new chat tab
        tab = ChatPane()
        self._open_or_focus_tab(tab)

    def action_extend_side_panel(self) -> None:
        self.layout_controller.adjust_side_panel(reduce=False)

    def action_reduce_side_panel(self) -> None:
        self.layout_controller.adjust_side_panel()

    def action_hide_top_bar(self) -> None:
        self.layout_controller.hide_top_bar()

    def action_unhide_top_bar(self) -> None:
        self.layout_controller.show_top_bar()

    def action_delete_selected_file(self) -> None:
        """Delete the selected file or folder and close any open document associated with it."""

        browser = self.query_one(".file-browser", expect_type=FileBrowser)
        deleted_path = browser.delete_selected_item()
        if not deleted_path:
            return

        closed_docs = self.documents.close_by_path(deleted_path)
        for doc_id in closed_docs:
            self.tabbed_editor.remove_pane(doc_id)

        # send notify and refresh file browser
        self.notify(f"Deleted {str(deleted_path)}")
        browser.reload()

    def action_save_file(self) -> None:
        """
        Save the currently active document.

        If the active tab represents a document managed by DocumentContext,
        the document is saved to disk. If the document has not been saved
        before, the user is prompted to choose a save location.

        Non-document tabs (e.g. welcome screen, shortcuts, AI chat) are ignored.
        """

        document = self._get_active_document()

        if document.path is None:
            # finalize untitled document
            file_path = self.file_workflow.save_as(document)
            if not file_path:
                return

            self.notify(f"File saved to {file_path}")

            # replace tab for unsaved document and reload file browser
            self.tabbed_editor.remove_pane(document.id)

            self.open_file_in_tab(file_path)

            self._show_file_browser_at(file_path.parent)
        else:
            self.file_workflow.save_existing_document(document)
            self.notify(f"Saved {document.title}")

    def _get_active_document(self) -> Optional[Document]:
        """Return the Document associated with the currently active tab, if any."""

        tab = self.tabbed_editor.active_pane
        if not tab:
            return None

        return self.documents.try_get(tab.id)

    def _show_file_browser_at(self, path: Path) -> None:
        """Navigate the file browser to the given path and make it visible."""

        browser = self.query_one(".file-browser", expect_type=FileBrowser)
        browser.path = Path(path).resolve()
        browser.reload()
        self.layout_controller.show_side_panel(SidePanelId.FILE_BROWSER)

    def action_save_file_as(self) -> None:
        """
        Save the currently active document under a new file path.

        If the active tab represents a document managed by DocumentContext,
        the user is prompted to choose a new save location. The document is
        then persisted to disk and its identity (path, title, dirty state)
        is updated accordingly.

        Non-document tabs are ignored.
        """

        document = self._get_active_document()

        file_path = self.file_workflow.save_as(document)
        if not file_path:
            return

        self.notify(f"Saved as {file_path}")

        folder_path = file_path.parent
        self._show_file_browser_at(folder_path)

    def action_close_tab(self) -> None:
        """
        Close the currently active tab.

        If the active tab corresponds to a document managed by DocumentContext and
        the document has unsaved changes, the user is prompted to save before the
        tab is closed.

        Tabs that do not represent documents (e.g. welcome screen, key mappings,
        AI chat) are closed immediately without any save prompt.
        """

        self.file_workflow.close_active_tab(self.tabbed_editor,
                                            self.tab_lifecycle)
        self.query_one(".file-browser", expect_type=FileBrowser).reload()

    def action_quit(self) -> None:
        """
        Quit the application, prompting to save unsaved document changes if needed.

        This method iterates over all open tabs and checks whether each tab represents
        a document managed by DocumentContext. For document tabs with unsaved changes,
        the user is prompted to confirm saving before the application exits.

        Non-document tabs (e.g. welcome screen, key mappings, AI chat) are ignored.
        """

        self.file_workflow.confirm_and_close_all_tabs(self.tabbed_editor,
                                                      self.tab_lifecycle)

        OllamaClient.shutdown()
        self.exit()

    def action_run_script(self) -> None:
        """
        Run the currently active document using a temp file.

        The document is NOT auto-saved. Unsaved changes are written to a
        temporary file under ~/.catnip/tmp and executed from there.
        """

        file_path = get_runnable_file(self.tabbed_editor, self.documents)
        if not file_path:
            return

        self.action_show_runner_panel()
        runner_output = self.query_one("#runner-output", expect_type=RichLog)
        output = runner.run_file(file_path)
        runner_output.write(f"{output}\n➜ ✗ (catnip):")

    def open_file_dialog(self) -> None:
        """Open a file selection dialog and open the selected files in editor tabs."""

        file_paths = self.dialog_handler.select_file()
        if not file_paths:
            return

        for file in file_paths:
            self.open_file_in_tab(file)

        folder_path = file_paths[0].parent
        self._show_file_browser_at(folder_path)

    def open_folder_dialog(self) -> None:
        """Open a folder selection dialog and load it into the file browser."""

        folder_path = self.dialog_handler.select_folder()
        if not folder_path:
            return

        self._show_file_browser_at(folder_path)

    def open_file_in_tab(self, file_path: Path) -> None:
        """
        Open a file in the editor as a tab.

        This method delegates document loading and lifecycle management to
        DocumentContext. If the file is already open, the existing tab is
        activated. Otherwise, a new editor tab is created and populated
        with the file content.
        """

        document = self.documents.open(file_path.resolve())

        tab = TabPane(id=document.id, title=document.title)
        self._open_or_focus_tab(tab, document)

    def create_a_file(self) -> None:
        """
        Create a new untitled document and open it in the editor.

        This method delegates untitled document creation to DocumentContext,
        then creates a corresponding editor tab and mounts a text editor
        initialized with the document's default state.
        """

        document = self.documents.create_untitled()

        tab = TabPane(id=document.id, title=document.title)

        self.tabbed_editor.add_pane(tab)
        self.call_after_refresh(
            lambda: self._mount_editor_for_document(tab, document))

        self.tabbed_editor.active = tab.id

    def _mount_editor_for_document(self, tab: TabPane, document) -> None:
        """Create and mount an Editor widget for the given document inside the provided tab."""

        text_area = Editor.for_document(document_id=document.id,
                                        controller=self.editor_controller,
                                        language=document.language or "markdown",
                                        soft_wrap=True, )
        register_custom_editor_theme(text_area)
        text_area.theme = self.editor_theme
        text_area.load_text(document.content or "")

        tab.mount(text_area)

    def _open_or_focus_tab(self,
                           tab: TabPane,
                           document: DocumentContext = None):
        """Open a new tab or focus an existing one, mounting an editor if a document is provided."""

        if not is_open(tab.id, self.tabbed_editor):
            self.tabbed_editor.add_pane(tab)
            if document is not None:
                self.call_after_refresh(
                    lambda: self._mount_editor_for_document(tab, document))

        self.tabbed_editor.active = tab.id


if __name__ == "__main__":
    app = CatnipApp()
    app.run()
