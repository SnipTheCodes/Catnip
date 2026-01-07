# constants.py
from rich.style import Style
from textual.theme import BUILTIN_THEMES
from textual.theme import Theme
from textual.widgets import TextArea
from textual.widgets.text_area import TextAreaTheme

# width sizes for side panel and tabbed editor in percentages
WIDTH_SCALES = [0, 0.25, 0.5, 1]
DEFAULT_SIDE_PANEL_WIDTH_PERCENTAGE = WIDTH_SCALES[1]

# welcome message displayed in the app
WELCOME_MESSAGE = """
### 😻 Purr purr, welcome to Catnip! 😻
- **Adjust** your terminal size for better view.
- **Hover over** a button to see its tooltip.
- **🐳 Ctrl+2** to open a customizer panel and change the look.
- **🐱 Ctrl+Shift+C** to start chatting with a cat.

### 📌 Supported Syntax Highlight:
>Python, JSON, Markdown, YAML, TOML, Rust,  
>
>HTML, CSS, XML, SQL, JavaScript, TypeScript, 
>
>Java, Bash, and Go.
"""

EXCEPTION_TAB_IDS = ("key-mappings", "welcome", "cat-me")

# available themes for the app
APP_THEMES = sorted(
    [("Catnip", "catnip")]
    + [(theme.replace("-", " ").title(), theme) for theme in
       BUILTIN_THEMES.keys()],
    key=lambda x: x[0]
)

# available themes for the editor
EDITOR_THEMES = sorted(
    [("Catnip", "catnip")]
    + [(theme.name.replace("_", " ").title(), theme.name) for theme in
       TextAreaTheme.builtin_themes()],
    key=lambda x: x[0])

# builtin languages for syntax highlighting
text_area = TextArea()
LANGUAGES = list(text_area.available_languages) + ["typescript"]
RUNNER_SUPPORTED_LANGUAGES = ["js", 'ts', "py", "java"]

_CATNIP = Theme(
    name="catnip",
    primary="#2980b9",
    secondary="#1abc9c",
    accent="#27ae60",
    foreground="#abb2bf",
    background="#34495e",
    success="#27ae60",
    warning="#f39c12",
    error="#e74c3c",
    surface="#21252b",
    panel="#333842",
    dark=True,
    variables={
        "block-cursor-text-style": "none",
        "footer-key-foreground": "#2ba143",
        "input-selection-background": "#3e4451",
    },
)

_CATNIP_EDITOR = TextAreaTheme(
    name="catnip",
    base_style=Style(color="#abb2bf", bgcolor="#282c34"),
    gutter_style=Style(color="#636d83", bgcolor="#21252b"),
    cursor_style=Style(color="#282c34", bgcolor="#528bff"),
    cursor_line_style=Style(bgcolor="#2c313a"),
    bracket_matching_style=Style(bgcolor="#3a3f4b", bold=True),
    cursor_line_gutter_style=Style(color="#abb2bf", bgcolor="#2c313a"),
    selection_style=Style(bgcolor="#3e4451"),
    syntax_styles={
        "string": Style(color="#98c379"),
        "string.documentation": Style(color="#98c379"),
        "comment": Style(color="#5c6370"),
        "heading.marker": Style(color="#d19a66"),
        "keyword": Style(color="#c678dd"),
        "keyword.self": Style(color="#c678dd"),
        "operator": Style(color="#56b6c2"),
        "conditional": Style(color="#e06c75"),
        "keyword.function": Style(color="#c678dd"),
        "keyword.return": Style(color="#56b6c2"),
        "keyword.operator": Style(color="#c678dd"),
        "repeat": Style(color="#e06c75"),
        "exception": Style(color="#e06c75"),
        "include": Style(color="#c678dd"),
        "number": Style(color="#d19a66"),
        "float": Style(color="#d19a66"),
        "class": Style(color="#c678dd"),
        "type": Style(color="#e5c07b"),
        "type.class": Style(color="#e5c07b"),
        "type.builtin": Style(color="#56b6c2"),
        "variable.builtin": Style(color="#BDC3C7"),
        "function": Style(color="#56b6c2"),
        "function.call": Style(color="#56b6c2"),
        "method": Style(color="#61afef"),
        "method.call": Style(color="#61afef"),
        "constructor": Style(color="#e5c07b"),
        "boolean": Style(color="#56b6c2"),
        "constant.builtin": Style(color="#d19a66"),
        "json.null": Style(color="#d19a66"),
        "tag": Style(color="#e06c75"),
        "yaml.field": Style(color="#61afef", bold=True),
        "json.label": Style(color="#61afef", bold=True),
        "toml.type": Style(color="#e5c07b"),
        "toml.datetime": Style(color="#c678dd", italic=True),
        "css.property": Style(color="#e5c07b"),
        "heading": Style(color="#c678dd", bold=True),
        "bold": Style(bold=True),
        "italic": Style(italic=True),
        "strikethrough": Style(strike=True),
        "link.uri": Style(color="#56b6c2", underline=True),
        "link.label": Style(color="#c678dd"),
        "list.marker": Style(color="#d19a66"),
        "inline_code": Style(color="#d19a66"),
        "info_string": Style(color="#d19a66", bold=True, italic=True),
        "punctuation.bracket": Style(color="#abb2bf"),
        "punctuation.delimiter": Style(color="#abb2bf"),
        "punctuation.special": Style(color="#abb2bf"),
        "html.end_tag_error": Style(color="#E06C75", bold=True, underline=True),
        "regex.operator": Style(color="#56B6C2", bold=True),
        "regex.punctuation.bracket": Style(color="#D19A66"),
    },
)

CUSTOM_EDITOR_THEMES: list[TextAreaTheme] = [_CATNIP_EDITOR]
CUSTOM_APP_THEMES: list[Theme] = [_CATNIP]
