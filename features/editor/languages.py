from textual.widgets import TextArea

from .constants import EXTENSION_LANGUAGE_MAP

_BUILTIN_LANGUAGES = set(TextArea().available_languages)


def supported_languages() -> set[str]:
    """Languages supported by the editor."""
    return _BUILTIN_LANGUAGES | set(EXTENSION_LANGUAGE_MAP.values())


def resolve_language(extension: str) -> str:
    """Resolve a file extension to a valid editor language."""
    language = EXTENSION_LANGUAGE_MAP.get(extension.lower())
    return language if language in supported_languages() else "markdown"
