import shutil
from datetime import datetime
from pathlib import Path
from typing import Union

from textual.widgets import DirectoryTree, Tree


class FileBrowser(DirectoryTree):
    """Directory tree widget for browsing, opening, and deleting files."""

    ICON_FILE = "🏷️ "
    ICON_NODE = "📒 "
    ICON_NODE_EXPANDED = "📒 "

    def __init__(self, path: Union[str, Path] = "./", on_open_file=None,
                 on_confirm_delete=None, ) -> None:
        super().__init__(path, id="file-browser", classes="file-browser")
        self.selected_path = None
        self.last_click_time = None
        self.on_open_file = on_open_file
        self.on_confirm_delete = on_confirm_delete

    def on_directory_tree_file_selected(self,
                                        event: DirectoryTree.FileSelected) -> None:
        """Handle file selection and trigger open action on double-click."""

        event.stop()
        current_time = datetime.now().timestamp()
        if self.last_click_time and (current_time - self.last_click_time) < 0.5:
            self.selected_path = Path(event.path)
            if self.on_open_file:
                self.on_open_file(self.selected_path)
        self.last_click_time = current_time

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Track the currently highlighted file or folder in the tree."""

        event.stop()
        self.selected_path = Path(event.node.data.path)

    def delete_selected_item(self) -> Path:
        """Delete the currently selected file or folder after confirmation."""

        if not self.selected_path or not self.selected_path.name:
            return None

        if self.on_confirm_delete:
            confirm = self.on_confirm_delete(title="Delete Confirmation",
                                             message="Are you sure you want to delete {}'{}'?".format(
                                                 "folder " if self.selected_path.is_dir() else "",
                                                 self.selected_path.name, ), )
            if not confirm:
                return None

        try:
            if self.selected_path.is_file():
                self.selected_path.unlink()
            else:
                shutil.rmtree(self.selected_path)
            self.reload()
            return self.selected_path
        except Exception as e:
            self.notify(f"Error deleting file: {e}", severity="error")
