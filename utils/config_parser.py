import json
from pathlib import Path


class ConfigParser:
    """Handles loading, updating, and saving configuration settings."""

    CONFIG_DIR = Path.home() / ".config" / "catnip"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    DEFAULT_CONFIG = {
        "api_key": "",
        "app_theme": "nord",
        "editor_theme": "atom_dark"
    }

    @classmethod
    def _ensure_config_exists(cls):
        """Ensure the config directory and file exist."""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if not cls.CONFIG_FILE.exists():
            cls.save_config(cls.DEFAULT_CONFIG)

    @classmethod
    def load_config(cls) -> dict:
        """Load the configuration from the config file."""
        cls._ensure_config_exists()
        try:
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return cls.DEFAULT_CONFIG

    @classmethod
    def get(cls, key: str, default=None):
        """Retrieve a config value."""
        config = cls.load_config()
        return config.get(key, default)

    @classmethod
    def save_config(cls, config: dict) -> None:
        """Save the config to the file."""
        with open(cls.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)

    @classmethod
    def update_config_file(cls, field: str, value: str) -> None:
        config = cls.load_config()
        config[field] = value
        cls.save_config(config)
