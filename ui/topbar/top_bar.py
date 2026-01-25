from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button


class TopBar(Container):
    """The top bar containing file operation buttons"""

    def __init__(self):
        super().__init__()

    def compose(self) -> ComposeResult:
        """Create the top bar layout."""
        yield Horizontal(Button("Open Folder", id="open-folder",
                                classes="option open-folder",
                                tooltip="Ctrl+Shift+O"),
                         Button("Open Files", id="open-file",
                                classes="option open-file", tooltip="Ctrl+O"),
                         Button("New File", id="new-file",
                                classes="option new-file", tooltip="Ctrl+N"),
                         classes="top-bar", )
