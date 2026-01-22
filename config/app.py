import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class AppConfig:
    app_theme: str = "dracula"
    editor_theme: str = "dracula"
    use_llm: bool = True
    llm_on_start: bool = False

    CONFIG_DIR = Path.home() / ".config" / "catnip"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    @classmethod
    def load(cls) -> "AppConfig":
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if not cls.CONFIG_FILE.exists():
            return cls()

        try:
            with open(cls.CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return cls()

        return cls(**data)

    def save(self) -> None:
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=4)
