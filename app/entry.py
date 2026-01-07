import asyncio
import random
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Union, cast

from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Button, Static, Footer, DirectoryTree, Select, TextArea, TabbedContent, TabPane, Markdown, \
    DataTable, ContentSwitcher, Tree, RichLog, LoadingIndicator
from app import runner
from app.ai import OllamaAI
from app.constants import WELCOME_MESSAGE, APP_THEMES, EDITOR_THEMES, CUSTOM_EDITOR_THEMES, \
    CUSTOM_APP_THEMES, EXCEPTION_TAB_IDS, LANGUAGES, WIDTH_SCALES, \
    DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE, RUNNER_SUPPORTED_LANGUAGES
from app.editor import Editor
from app.explorer import get_dialog_handler
from app.utils.config_parser import ConfigParser
from app.utils.screen import DEFAULT_LEFT_PANEL_WIDTH, get_side_panel_width, get_tabbed_editor_width, \
    DEFAULT_TABBED_EDITOR_WIDTH


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


class TopBar(Container):
    """The top bar containing file operation buttons, a spinner, and a clock."""

    def __init__(self):
        super().__init__()
        self.date_widget = None
        self.clock_widget = None

    def compose(self) -> ComposeResult:
        """Create the top bar layout."""
        yield Horizontal(
            Button("Open Folder", id="open-folder",
                   classes="option open-folder", tooltip="Ctrl+Shift+O"),
            Button("Open Files", id="open-file",
                   classes="option open-file", tooltip="Ctrl+O"),
            Button("New File", id="new-file",
                   classes="option new-file", tooltip="Ctrl+N"),
            classes="top-bar",
        )


class FileBrowser(DirectoryTree):
    """Custom directory tree for browsing files and folders."""

    # Set custom icons before initializing the tree
    ICON_FILE = "🏷️ "
    ICON_NODE = "📒 "
    ICON_NODE_EXPANDED = "📒 "

    def __init__(self, path: Union[str, Path] = "./") -> None:
        """Initialize the file browser with a given path."""
        super().__init__(path, id="file-browser")
        self.selected_path = None
        self.last_click_time = None

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Detect selection on a file to open it."""
        event.stop()
        current_time = datetime.now().timestamp()
        if self.last_click_time and (current_time - self.last_click_time) < 0.5:
            catnip = cast(CatnipApp, self.app)
            self.selected_path = Path(event.path)
            catnip.open_file_in_tab(self.selected_path)
        self.last_click_time = current_time

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Highlight the selected file or folder."""
        event.stop()
        self.selected_path = Path(event.node.data.path)

    def delete_selected_item(self) -> None:
        """Delete the selected file or folder with confirmation."""
        if not self.selected_path.name:
            return

        # ask for confirmation before deletion
        catnip = cast(CatnipApp, self.app)
        confirm = catnip.dialog_handler.confirm_action(
            title="Delete Confirmation",
            message="Are you sure you want to delete {}'{}'?".format(
                'folder ' if self.selected_path.is_dir() else '', self.selected_path.name),
        )

        if not confirm:
            return  # do nothing if user cancels

        try:
            if self.selected_path.is_file():
                self.selected_path.unlink()  # delete file
            elif self.selected_path.is_dir():
                shutil.rmtree(self.selected_path)  # delete folder

            # reload the FileBrowser to reflect the change
            self.reload()
        except Exception as e:
            self.notify(f"Error deleting file: {e}", severity="error")


def _get_tab_id_from_path(file_path: Union[str, Path]) -> str:
    """Generate a unique tab ID based on the file path."""
    if isinstance(file_path, str):
        file_path = Path(file_path)
    return re.sub(r'[^a-zA-Z0-9]', '-', file_path.name).lower()


def _untitled_tab_has_content(tab: TabPane) -> bool:
    return tab.id.startswith("untitled") and tab.query_one(TextArea).text.strip()


def _create_mapping_table(table: DataTable, bindings: list) -> DataTable:
    bindings = sorted(bindings, key=lambda x: x[0])
    accent_color = app.get_css_variables()["accent"]
    for action, shortcut in bindings:
        styled_action = Text(str(action), justify="left")
        styled_shortcut = Text(
            str(shortcut), style=f"{accent_color}", justify="left")
        table.add_row(styled_action, styled_shortcut)

    return table


def _regis_custom_editor_theme(text_area: TextArea) -> None:
    for theme in CUSTOM_EDITOR_THEMES:
        text_area.register_theme(theme)


def _update_config_file(field: str, value: str) -> None:
    config = ConfigParser.load_config()
    config[field] = value
    ConfigParser.save_config(config)


class ChatPane(TabPane):
    """A chat-box for interacting with AI via TogetherAI."""

    def __init__(self, title: str = "Cat Me", tab_id: str = "cat-me"):
        super().__init__(title=title, id=tab_id)
        self.text_area = None
        self.message = None

    def compose(self):
        """Create the chat UI layout."""
        yield Container(
            VerticalScroll(id="chat-log"),
            TextArea(classes="chat-input"),
            classes="chat-pane",
        )

    def on_mount(self):
        """Ensure the text area is focused when the chat opens."""
        self.text_area = self.query_one(TextArea)
        self.text_area.focus()

    def on_key(self, event: events.Key) -> None:
        if event.key == "shift+enter":
            user_message = self.text_area.text.strip()
            if user_message:
                catnip = cast(CatnipApp, self.app)
                text_log = catnip.query_one(TabbedContent).query_one("#chat-log")
                text_log.mount(Static(f"{user_message}", classes="user-message"))

                self.text_area.clear()
                self.run_worker(self._send_message(text_log, user_message))

    async def _send_message(self, text_log: RichLog, user_message: str):
        """Handles sending user input to LLM and displaying the response."""
        self.message = None

        try:
            # show loading animation while waiting for LLM response
            loading = LoadingIndicator()
            await text_log.mount(loading)

            # mount a live Markdown widget to update dynamically
            buffer = ""
            response_widget = Markdown("", classes="ai-message")
            await text_log.mount(response_widget)

            # stream response as it comes
            first_chunk = True
            async for chunk in OllamaAI.stream_response(user_message):
                if first_chunk:
                    await loading.remove()  # remove spinner only when response starts
                    first_chunk = False
                buffer += chunk
                await response_widget.update(buffer)
                text_log.scroll_end(animate=False)
                await asyncio.sleep(0)  # let UI refresh

        except Exception as e:
            await text_log.mount(Static(f"{e}", classes="ai-message"))


class CatnipApp(App):
    """Main application class to run the top bar screen."""

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
        """Initialize the CatnipApp with a dialog handler."""
        super().__init__()
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self.dialog_handler = get_dialog_handler()
        self.current_path = Path.cwd()
        self.theme_picker = None
        self.tabbed_editor = None
        self.opened_tabs = {}
        self.languages = LANGUAGES
        self.desc_key_pairs = [(b.description, b.key) for b in self.BINDINGS]

        # load config, register custom themes and apply
        self.app_theme = ConfigParser.get("app_theme", "atom_dark")
        self.editor_theme = ConfigParser.get("editor_theme", "atom_dark")
        for theme in CUSTOM_APP_THEMES:
            self.register_theme(theme)
        self.theme = self.app_theme

        self.file_browser = FileBrowser()
        self.customizer_panel = CustomizerPanel(
            APP_THEMES, self.app_theme, EDITOR_THEMES, self.editor_theme, self.languages)
        self.runner = RichLog(highlight=True, markup=True, wrap=True, id="runner-output", auto_scroll=True)

    def compose(self) -> ComposeResult:
        """Create the screen layout."""
        self.tabbed_editor = TabbedContent(
            classes="tabbed-editor", id="tabbed-editor")

        # create a "Welcome" tab with Markdown instructions
        welcome_tab = TabPane(title="Welcome", id="welcome")
        welcome_markdown = Markdown(WELCOME_MESSAGE, classes="welcome-md")

        def mount_welcome_markdown():
            """Mount the Markdown widget after the TabPane is fully attached."""
            welcome_tab.mount(welcome_markdown)

        self.call_after_refresh(lambda: self.tabbed_editor.add_pane(welcome_tab))  # ensure tabbed editor exists
        # mount Markdown safely
        self.call_after_refresh(mount_welcome_markdown)

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
        """Add class attribute to File Browser."""
        self.query_one(FileBrowser).classes = "file-browser"
        side_panel = self.query_one("#side-panel")
        tabbed_editor = self.query_one(".tabbed-editor")
        side_panel.styles.width = DEFAULT_LEFT_PANEL_WIDTH
        tabbed_editor.styles.width = DEFAULT_TABBED_EDITOR_WIDTH

        config = ConfigParser.load_config()
        if config.get("llm_on_start"):
            OllamaAI.serve()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button clicks for opening files/folders or switching panels."""
        side_panel = self.query_one("#side-panel")
        button_id = event.button.id
        # handle file and folder opening separately
        if button_id == "open-file":
            self.open_file_dialog()
            # switch to file browser panel
            side_panel.current = "file-browser"
            # if the side panel is hidden, show it again
            self._enable_side_panel(side_panel)
            return
        elif button_id == "open-folder":
            self.open_folder_dialog()
            side_panel.current = "file-browser"
            self._enable_side_panel(side_panel)
            return
        elif button_id == "new-file":
            self.create_a_file()
            side_panel.current = "customizer"
            self._enable_side_panel(side_panel)
            return
        elif button_id == "key-mapping":
            self.action_show_shortcuts()
            return
        elif button_id == "cat-me":
            self.action_open_ai_chat()
            return
        elif button_id == "runner":
            self.action_show_runner_panel()
            return

        # handle switching side panel
        side_panel_id_mapping = {
            "file-browser": "file-browser",
            "customizer": "customizer",
            "runner": "runner-output",
        }

        if button_id in side_panel_id_mapping:
            # switch active panel
            side_panel.current = side_panel_id_mapping[button_id]
            self._enable_side_panel(side_panel)
            if side_panel.current == "file-browser":
                # reload file browser
                self.query_one(FileBrowser).reload()

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle selection changes in the Customizer Panel."""

        select_id = event.select.id  # get the ID of the changed select widget
        selected_value = event.value  # get the selected value

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

    def action_open_file(self) -> None:
        self.open_file_dialog()

    def action_open_folder(self) -> None:
        self.open_folder_dialog()

    def action_new_file(self) -> None:
        self.create_a_file()

    def action_open_ai_chat(self) -> None:
        """Start the LLM, the open or switch to the Cat Me tab."""
        OllamaAI.serve()
        tab_id = "cat-me"

        # check if the chat tab is already open
        if tab_id in self.opened_tabs:
            self.tabbed_editor.active = tab_id
            return

        # create and add the new chat tab
        chat_tab = ChatPane()
        self.tabbed_editor.add_pane(chat_tab)
        self.tabbed_editor.active = tab_id
        self.opened_tabs[tab_id] = None

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
        """Open the key mappings inside a new tab in the tabbed editor."""
        tab_id = "key-mappings"
        tabbed_editor = self.query_one(".tabbed-editor")
        # check if the tab already exists
        if tab_id in self.opened_tabs:
            tabbed_editor.active = tab_id
            return

        # create a new tab for key mappings
        tab = TabPane(title="Shortcuts", id=tab_id)

        # create a DataTable for key mappings
        table = DataTable(id="key-mapping-table")
        table.add_columns("Action", "Shortcut")
        table = _create_mapping_table(table, self.desc_key_pairs)

        def mount_table():
            """Mount the table inside the tab."""
            tab.mount(VerticalScroll(table))

        # add tab and mount content
        self.tabbed_editor.add_pane(tab)
        self.call_after_refresh(mount_table)

        # set active tab
        self.tabbed_editor.active = tab_id
        self.opened_tabs[tab_id] = [None, False]

    def action_extend_side_panel(self) -> None:
        """Extend the width of the side panel."""
        self.adjust_side_panel(is_reduce=False)

    def action_reduce_side_panel(self) -> None:
        """Reduce the width of the side panel."""
        self.adjust_side_panel()

    def adjust_side_panel(self, is_reduce: bool = True) -> None:
        """Adjust the width of the left side panel."""
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
        """Hide the Top Bar."""
        main_screen = self.query_one(".main-screen")
        top_bar = self.query_one(".top-bar")

        if top_bar.display:
            top_bar.display = False
            main_screen.add_class("expanded")

    def action_unhide_top_bar(self) -> None:
        """Unhide the Top Bar."""
        main_screen = self.query_one(".main-screen")
        top_bar = self.query_one(".top-bar")

        if not top_bar.display:
            top_bar.display = True
            main_screen.remove_class("expanded")

    def action_delete_selected_file(self) -> None:
        """Delete the selected file in FileBrowser."""
        self.query_one(FileBrowser).delete_selected_item()

    def action_save_file(self) -> None:
        """Save the current file. If it's a new file, prompt the user to select a save location."""
        dialog_handler = get_dialog_handler()
        active_tab = self.tabbed_editor.active_pane

        if not active_tab:
            self.notify("No active tab to save.", severity="warning")
            return

        text_area = active_tab.query_one(TextArea)
        file_content = text_area.text
        active_tab_id = active_tab.id  # get the tab id

        # if file is new (Untitled), prompt save dialog
        if active_tab_id.startswith("untitled"):
            file_path = dialog_handler.select_folder_save()
            if not file_path:
                pass

            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)
                self.notify(f"File saved to {file_path}")

                # open the saved file in new tab
                self.open_file_in_tab(file_path)

                # remove old tab
                self.tabbed_editor.remove_pane(active_tab_id)
                self.opened_tabs.pop(active_tab_id, None)

                # refresh file browser after saving a new file
                self.query_one(FileBrowser).reload()

                # open the file browser
                side_panel = self.query_one("#side-panel")
                side_panel.current = "file-browser"
                self._enable_side_panel(side_panel)

            except Exception as e:
                print(f"Failed to save file: {str(e)}")
        else:
            # if it's an existing file, just save
            file_path = self.opened_tabs.get(active_tab.id)
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(file_content)

                # refresh file browser
                self.query_one(FileBrowser).reload()
            except Exception as e:
                self.notify(f"Failed to save file: {str(e)}", severity="error")

    def action_save_file_as(self) -> None:
        """Prompt user to choose a new filename and save."""
        active_tab = self.tabbed_editor.active_pane
        text_area = active_tab.query_one(TextArea)

        # open Save As dialog
        new_file_path = self.dialog_handler.select_file_save()

        try:
            with open(new_file_path, "w", encoding="utf-8") as f:
                f.write(text_area.text)
            self.notify(f"File saved at: {new_file_path}")

            # update tracking to recognize this as a saved file
            self.opened_tabs[active_tab.id][0] = new_file_path
            active_tab.title = Path(new_file_path).name  # update tab title

            # refresh file browser after saving a new file
            self.query_one(FileBrowser).reload()
        except Exception as e:
            self.notify(f"ERROR: Failed to save file - {e}", severity="error")

    def action_close_tab(self) -> None:
        """Close the currently active tab."""
        active_tab = self.tabbed_editor.active_pane

        if not active_tab:
            return

        if active_tab.id not in EXCEPTION_TAB_IDS:
            # check if there are unsaved changes
            try:
                if self._is_tab_content_modified(active_tab):
                    confirm = self.dialog_handler.confirm_action(
                        title="Save Confirmation",
                        message=f"Do you want to save the changes you made in {active_tab.name}?",
                    )
                    if confirm:
                        self.action_save_file()

            except FileNotFoundError:
                pass

        # remove tab from tracking and UI
        self.tabbed_editor.remove_pane(active_tab.id)
        self.opened_tabs.pop(active_tab.id, None)

        # switch to last tab if exists
        if self.opened_tabs:
            self.tabbed_editor.active = next(reversed(self.opened_tabs))

    def action_quit(self) -> None:
        """Prompt to save changes before quitting."""
        for tab_id in reversed(list(self.opened_tabs.keys())):
            if tab_id not in ("key-mappings", "welcome"):
                tab = self.tabbed_editor.get_pane(tab_id)
                if self._is_tab_content_modified(tab):
                    self.tabbed_editor.active = tab_id

                    confirm = self.dialog_handler.confirm_action(
                        title="Unsaved Changes",
                        message=f"Do you want to save the changes you made in {tab.name}?",
                    )

                    if confirm:
                        self.action_save_file()
        self.exit()

    def action_run_script(self) -> None:
        """Run the current script in the active tab."""
        active_tab = self.tabbed_editor.active_pane

        # if no active tabs or active tab is non-executable, do nothing
        if not active_tab or active_tab.id in EXCEPTION_TAB_IDS:
            return

        text_area = active_tab.query_one(TextArea)
        file_content = text_area.text.strip()

        # if the file is empty, do nothing
        if not file_content:
            return

        # get file's extension from path
        file_path = self.opened_tabs.get(active_tab.id)
        file_ext = active_tab.id.split("-")[-1]

        runner_output = self.query_one("#side-panel").query_one("#runner-output", expect_type=RichLog)
        self.action_show_runner_panel()
        if file_ext in RUNNER_SUPPORTED_LANGUAGES:
            self.action_save_file()
            runner_output.write(f"{runner.run_script(file_path, file_ext)}\n➜ ✗ (catnip):")
        else:
            runner_output.write("Not supported file!\n➜ ✗ (catnip):")

    def apply_app_theme(self, app_theme: str) -> None:
        """Apply and save the selected app-wide theme."""

        self.theme = app_theme

        # save theme to project config
        _update_config_file("app_theme", app_theme)
        if "key-mappings" in self.opened_tabs:
            mappings_tab = self.tabbed_editor.get_pane("key-mappings")
            mappings_table = self.query_one("#key-mapping-table", expect_type=DataTable)
            mappings_table.clear()
            _create_mapping_table(mappings_table, self.desc_key_pairs)
            mappings_tab.refresh()

    def apply_editor_theme(self, theme: str) -> None:
        """Apply the selected theme to the code editor (syntax highlighting)."""

        for tab in self.tabbed_editor.query(TabPane):
            if tab.query(TextArea):
                text_area = tab.query_one(TextArea)
                _regis_custom_editor_theme(text_area)
                text_area.theme = theme

        # save theme to project config
        _update_config_file("editor_theme", theme)

    def apply_language(self, language: str) -> None:
        """Apply the selected language for syntax highlighting."""
        active_tab = self.tabbed_editor.active_pane
        if active_tab:
            if active_tab.id not in EXCEPTION_TAB_IDS:
                text_area = active_tab.query_one(TextArea)
                text_area.language = language if language != 'typescript' else 'javascript'  # change syntax highlighting

    def open_file_dialog(self) -> None:
        """Open a file selection dialog and update the DirectoryTree to its parent folder."""
        file_paths = self.dialog_handler.select_file()
        parent_folder = None
        if file_paths:
            for file in file_paths:
                self.open_file_in_tab(file)
                parent_folder = file_paths[0].parent
            # update DirectoryTree to the parent folder
            self.current_path = parent_folder.resolve()
            self.query_one(FileBrowser).path = str(self.current_path)

    def open_folder_dialog(self) -> None:
        """Open a folder selection dialog and update the DirectoryTree."""
        folder_path = self.dialog_handler.select_folder()
        if folder_path:
            self.current_path = Path(folder_path).resolve()
            self.query_one(FileBrowser).path = str(
                self.current_path)  # update directory tree

            # reload file browser after selecting a folder
            self.query_one(FileBrowser).reload()

    def open_file_in_tab(self, file_path: Path) -> None:
        """Open a file in a new tab inside TabbedContent."""
        file_path = file_path.resolve()
        tab_id = _get_tab_id_from_path(file_path)

        # prevent opening duplicate tabs
        if tab_id in self.opened_tabs:
            self.tabbed_editor.active = tab_id
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # detect file language
            language = Editor.get_file_language(file_path, self.languages)

            # create a new tab
            tab = TabPane(title=file_path.name, id=tab_id, name=file_path.name)

            def mount_textarea():
                """Mount the TextArea after the TabPane is fully loaded."""
                text_area = Editor.code_editor(
                    language=language, soft_wrap=True)
                _regis_custom_editor_theme(text_area)
                text_area.theme = self.editor_theme
                text_area.load_text(content)
                tab.mount(text_area)  # now mount TextArea safely

            self.tabbed_editor.add_pane(tab)  # add the new tab

            self.call_after_refresh(mount_textarea)  # ensure tab is mounted first

            # set the new tab as active
            self.tabbed_editor.active = tab_id

            self.opened_tabs[tab_id] = file_path  # track opened files

        except Exception:
            return

    def create_a_file(self) -> None:
        """Create a new blank tab inside the tabbed content."""

        # generate a unique tab name
        tab_index = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789", k=6))
        tab_name = "Untitled"
        tab_id = f"{tab_name}-{tab_index}".lower()

        # create a new text editor inside the tab
        text_area = Editor(id=tab_id,
                           language="markdown")
        _regis_custom_editor_theme(text_area)
        text_area.theme = self.editor_theme
        text_area.load_text("")

        # create and add the new tab
        new_tab = TabPane(title=tab_name, id=tab_id, name=tab_name)
        self.tabbed_editor.add_pane(new_tab)
        new_tab.mount(text_area)

        # set the new tab as active and add to opened tabs
        self.tabbed_editor.active = tab_id
        self.opened_tabs[tab_id] = None

    def _is_tab_content_modified(self, tab: TabPane) -> bool:
        if tab.id.startswith("untitled"):
            return _untitled_tab_has_content(tab)
        elif tab.id not in EXCEPTION_TAB_IDS:
            file_path = self.opened_tabs.get(tab.id)
            return Path(file_path).read_text(encoding="utf-8") != tab.query_one(TextArea).text
        return None

    def _enable_side_panel(self, side_panel: ContentSwitcher) -> None:
        if not side_panel.display:
            side_panel.display = True
            side_panel.styles.width = DEFAULT_LEFT_PANEL_WIDTH
            self.query_one(".tabbed-editor").styles.width = DEFAULT_TABBED_EDITOR_WIDTH
            self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE


if __name__ == "__main__":
    app = CatnipApp()
    app.run()
