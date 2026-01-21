from textual.containers import VerticalScroll
from textual.widgets import DataTable, TabPane

from utils.keymap import create_mapping_table


class ShortcutsTab(TabPane):
    def __init__(self, desc_key_pairs, accent_color: str):
        super().__init__(title="Shortcuts", id="key-mappings")
        self._desc_key_pairs = desc_key_pairs
        self._accent_color = accent_color

    def on_mount(self) -> None:
        table = DataTable(id="key-mapping-table")
        table.add_columns("Action", "Shortcut")
        create_mapping_table(table, self._desc_key_pairs, self._accent_color, )
        self.mount(VerticalScroll(table))
