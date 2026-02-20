from rich.style import Style
from textual.theme import BUILTIN_THEMES, Theme
from textual.widgets import TextArea
from textual.widgets.text_area import TextAreaTheme

APP_THEMES = sorted(
    [("Catnip", "catnip")] + [(theme.replace("-", " ").title(), theme) for theme
                              in
                              BUILTIN_THEMES.keys()], key=lambda x: x[0])

# available themes for the editor
EDITOR_THEMES = sorted(
    [("Catnip", "catnip")] + [(theme.replace("_", " ").title(), theme)
                              for theme in list(TextArea().available_themes)],
    key=lambda x: x[0])

_CATNIP = Theme(
    name="catnip",
    primary="#a6e3a1",      # pastel green
    secondary="#94e2d5",    # pastel teal
    accent="#fab387",       # pastel orange
    foreground="#e2e6de",   # warm off-white
    background="#1e1e2e",   # deep soft dark
    success="#a6e3a1",      # pastel green
    warning="#f9e2af",      # pastel amber
    error="#f38ba8",        # pastel rose
    surface="#252532",      # raised surface
    panel="#313244",        # panel / sidebar
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#a6e3a1",
        "input-selection-background": "#45475a",
    },
)

_CATNIP_EDITOR = TextAreaTheme(
    name="catnip",
    base_style=Style(color="#e2e6de", bgcolor="#1e1e2e"),
    gutter_style=Style(color="#6c7086", bgcolor="#252532"),
    cursor_style=Style(color="#1e1e2e", bgcolor="#a6e3a1"),
    cursor_line_style=Style(bgcolor="#252532"),
    bracket_matching_style=Style(bgcolor="#45475a", bold=True),
    cursor_line_gutter_style=Style(color="#e2e6de", bgcolor="#252532"),
    selection_style=Style(bgcolor="#45475a"),
    syntax_styles={
        "string": Style(color="#a6e3a1"),
        "string.documentation": Style(color="#a6e3a1"),
        "comment": Style(color="#6c7086"),
        "heading.marker": Style(color="#fab387"),
        "keyword": Style(color="#cba6f7"),
        "keyword.self": Style(color="#cba6f7"),
        "operator": Style(color="#94e2d5"),
        "conditional": Style(color="#f38ba8"),
        "keyword.function": Style(color="#cba6f7"),
        "keyword.return": Style(color="#94e2d5"),
        "keyword.operator": Style(color="#cba6f7"),
        "repeat": Style(color="#f38ba8"),
        "exception": Style(color="#f38ba8"),
        "include": Style(color="#cba6f7"),
        "number": Style(color="#fab387"),
        "float": Style(color="#fab387"),
        "class": Style(color="#cba6f7"),
        "type": Style(color="#f9e2af"),
        "type.class": Style(color="#f9e2af"),
        "type.builtin": Style(color="#94e2d5"),
        "variable.builtin": Style(color="#bac2de"),
        "function": Style(color="#94e2d5"),
        "function.call": Style(color="#94e2d5"),
        "method": Style(color="#94e2d5"),
        "method.call": Style(color="#94e2d5"),
        "constructor": Style(color="#f9e2af"),
        "boolean": Style(color="#94e2d5"),
        "constant.builtin": Style(color="#fab387"),
        "json.null": Style(color="#fab387"),
        "tag": Style(color="#f38ba8"),
        "yaml.field": Style(color="#a6e3a1", bold=True),
        "json.label": Style(color="#a6e3a1", bold=True),
        "toml.type": Style(color="#f9e2af"),
        "toml.datetime": Style(color="#cba6f7", italic=True),
        "css.property": Style(color="#f9e2af"),
        "heading": Style(color="#cba6f7", bold=True),
        "bold": Style(bold=True),
        "italic": Style(italic=True),
        "strikethrough": Style(strike=True),
        "link.uri": Style(color="#94e2d5", underline=True),
        "link.label": Style(color="#cba6f7"),
        "list.marker": Style(color="#fab387"),
        "inline_code": Style(color="#fab387"),
        "info_string": Style(color="#fab387", bold=True, italic=True),
        "punctuation.bracket": Style(color="#e2e6de"),
        "punctuation.delimiter": Style(color="#e2e6de"),
        "punctuation.special": Style(color="#e2e6de"),
        "html.end_tag_error": Style(color="#f38ba8", bold=True, underline=True),
        "regex.operator": Style(color="#94e2d5", bold=True),
        "regex.punctuation.bracket": Style(color="#fab387"),
    },
)

CUSTOM_EDITOR_THEMES: list[TextAreaTheme] = [_CATNIP_EDITOR]
CUSTOM_APP_THEMES: list[Theme] = [_CATNIP]
