from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import Button


class SideBar(Container):
    """
    The sidebar containing operation buttons such as file browser, customizer,
    runner, key mapping, and cat me.
    """

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create the sidebar layout."""

        yield Container(Button("📦", id="file-browser",
                               tooltip="Show directory tree panel (Ctrl+1)"),
                        Button("⚙️ ", id="customizer",
                               tooltip="Show customizer panel (Ctrl+2)"),
                        Button("▶️", id="runner", tooltip="Runner (Ctrl+3)"),
                        Button("🍀", id="key-mapping",
                               tooltip="Show key mappings (Ctrl+4)"),
                        Button("🐱", id="cat-me",
                               tooltip="Cat me (Ctrl+Shift+C)"),
                        classes="side-button")
