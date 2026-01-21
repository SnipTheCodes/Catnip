from rich.text import Text
from textual.widgets import DataTable


def create_mapping_table(table: DataTable, bindings: list,
                         accent_color: str, ) -> DataTable:
    bindings = sorted(bindings, key=lambda x: x[0])
    for action, shortcut in bindings:
        table.add_row(Text(str(action), justify="left"),
                      Text(str(shortcut), style=accent_color, justify="left"))
    return table
