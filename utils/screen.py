import shutil


def get_side_panel_width(percentage: int) -> int:
    """Get the width of the left panel in the terminal."""
    return int(get_terminal_width() * percentage)


def get_tabbed_editor_width(side_panel_width: int) -> int:
    """Get the width of the tabbed editor in the terminal."""
    terminal_width = get_terminal_width()
    return terminal_width - side_panel_width


def get_terminal_width() -> int:
    """Get the current terminal width."""
    return shutil.get_terminal_size().columns - 6  # subtracting 6 for 2 paddings and side icon


DEFAULT_LEFT_PANEL_WIDTH = get_side_panel_width(0.25)
DEFAULT_TABBED_EDITOR_WIDTH = get_tabbed_editor_width(DEFAULT_LEFT_PANEL_WIDTH)
