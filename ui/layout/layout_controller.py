from ui.constants import WIDTH_SCALES, DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
from ui.sidebar.sidebar import SideBar
from utils.screen import get_side_panel_width, get_tabbed_editor_width


class LayoutController:
    def __init__(self, app: "CatnipApp"):
        self.app = app
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE

    def show_side_panel(self, panel_id: str) -> None:
        side_panel = self._get_side_panel()
        side_panel.current = panel_id
        side_panel.display = True
        self.side_panel_width_percentage = DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE
        self._apply_layout()

    def adjust_side_panel(self, reduce: bool = True) -> None:
        index = WIDTH_SCALES.index(self.side_panel_width_percentage)
        next_index = index - 1 if reduce else index + 1

        if 0 <= next_index < len(WIDTH_SCALES):
            self.side_panel_width_percentage = WIDTH_SCALES[next_index]

        side_panel = self._get_side_panel()
        side_panel.display = self.side_panel_width_percentage != min(WIDTH_SCALES)

        self._apply_layout()

    def hide_top_bar(self) -> None:
        top_bar = self.app.query_one(".top-bar")
        main_screen = self.app.query_one(".main-screen")
        top_bar.display = False
        main_screen.add_class("expanded")

    def show_top_bar(self) -> None:
        top_bar = self.app.query_one(".top-bar")
        main_screen = self.app.query_one(".main-screen")
        top_bar.display = True
        main_screen.remove_class("expanded")

    def _apply_layout(self) -> None:
        side_panel = self._get_side_panel()
        tabbed_editor = self.app.query_one(".tabbed-editor")

        if not side_panel.display:
            tabbed_editor.styles.width = "100%"
            return

        side_panel_width = get_side_panel_width(self.side_panel_width_percentage)
        side_panel.styles.width = side_panel_width
        tabbed_editor.styles.width = get_tabbed_editor_width(side_panel_width)

    def _get_side_panel(self) -> SideBar:
        return self.app.query_one("#side-panel")
