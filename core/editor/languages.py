from textual.widgets import TextArea

_BUILTIN_LANGUAGES = set(TextArea().available_languages)

EXTENSION_LANGUAGE_MAP = {"py": "python", "md": "markdown", "json": "json",
                          "toml": "toml", "yaml": "yaml",
                          "yml": "yaml", "html": "html", "css": "css",
                          "js": "javascript", "ts": "javascript", "rs": "rust",
                          "go": "go",
                          "sql": "sql", "java": "java", "sh": "bash",
                          "bash": "bash", "xml": "xml", }

LANGUAGE_EXTENSION_MAP = {v: k for k, v in EXTENSION_LANGUAGE_MAP.items()}


def supported_languages() -> set[str]:
    """Languages supported by the editor."""
    return _BUILTIN_LANGUAGES | set(EXTENSION_LANGUAGE_MAP.values())


def resolve_language(extension: str) -> str:
    """Resolve a file extension to a valid editor language."""
    language = EXTENSION_LANGUAGE_MAP.get(extension.lower())
    return language if language in supported_languages() else "markdown"
