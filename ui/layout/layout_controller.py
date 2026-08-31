from enum import Enum
from typing import TYPE_CHECKING

from ui.constants import WIDTH_SCALES, DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
from ui.sidebar.sidebar import SideBar
from utils.screen import get_side_panel_width, get_tabbed_editor_width

if TYPE_CHECKING:
    from app.entry import CatnipApp


class SidePanelId(Enum):
    FILE_BROWSER = "file-browser"
    CUSTOMIZER = "customizer"
    RUNNER_OUTPUT = "runner-output"


class LayoutController:
    """Control layout changes for the side panel and top bar based on user actions."""

    def __init__(self, app: "CatnipApp"):
        self.app = app
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE

    def show_side_panel(self, panel_id: SidePanelId) -> None:
        """Display the given side panel and reset it to the default width."""

        side_panel = self._get_side_panel()
        side_panel.current = panel_id.value
        side_panel.display = True
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self._apply_layout()

    def adjust_side_panel(self, reduce: bool = True) -> None:
        """Increase or decrease the side panel width based on predefined scales."""

        index = WIDTH_SCALES.index(self.side_panel_width_percentage)
        next_index = index - 1 if reduce else index + 1

        if 0 <= next_index < len(WIDTH_SCALES):
            self.side_panel_width_percentage = WIDTH_SCALES[next_index]

        side_panel = self._get_side_panel()
        side_panel.display = self.side_panel_width_percentage != min(
            WIDTH_SCALES)

        self._apply_layout()

    def hide_top_bar(self) -> None:
        """Hide the top bar and expand the main screen area."""

        self.app.query_one(".top-bar").display = False
        self.app.query_one(".main-screen").add_class("expanded")

    def show_top_bar(self) -> None:
        """Show the top bar and restore the main screen layout."""

        self.app.query_one(".top-bar").display = True
        self.app.query_one(".main-screen").remove_class("expanded")

    def _apply_layout(self) -> None:
        """Apply the current side panel width to the layout."""

        side_panel = self._get_side_panel()
        tabbed_editor = self.app.query_one(".tabbed-editor")

        if not side_panel.display:
            # Keep the icon rail visible and let the editor fill only the
            # horizontal space that remains after it.
            tabbed_editor.styles.width = "1fr"
            return

        side_panel_width = get_side_panel_width(
            self.side_panel_width_percentage)
        side_panel.styles.width = side_panel_width
        tabbed_editor.styles.width = get_tabbed_editor_width(side_panel_width)

    def _get_side_panel(self) -> SideBar:
        """Return the side panel widget instance."""

        return self.app.query_one("#side-panel")
