from __future__ import annotations

import json
from pathlib import Path


class Settings:
    DEFAULTS = {
        "window_width": 1500,
        "window_height": 950,
        "recent_files": [],
        "theme": "dark",
    }

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path.home() / ".ordpaint.json"
        self.data = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            if self.path.exists():
                saved = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(saved, dict):
                    self.data.update(saved)
        except (OSError, json.JSONDecodeError):
            pass

    def save(self) -> None:
        try:
            self.path.write_text(json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        self.data[key] = value

    def add_recent_file(self, path: str) -> None:
        files = [item for item in self.data.get("recent_files", []) if item != path]
        self.data["recent_files"] = [path, *files][:10]
