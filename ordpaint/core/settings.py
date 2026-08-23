from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


class Settings:
    DEFAULTS = {
        "window_width": 1500,
        "window_height": 950,
        "recent_files": [],
        "theme": "dark",
        "last_directory": "",
        "show_tool_labels": True,
        "canvas_background": "#ffffff",
    }

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else Path.home() / ".ordpaint.json"
        self.data: dict[str, Any] = dict(self.DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            saved = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}
        except (OSError, json.JSONDecodeError):
            return
        if not isinstance(saved, dict):
            return
        for key, value in saved.items():
            if key in self.DEFAULTS and isinstance(value, type(self.DEFAULTS[key])):
                self.data[key] = value
        recent = self.data.get("recent_files", [])
        self.data["recent_files"] = [str(path) for path in recent if isinstance(path, str)]

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
            ) as temporary:
                json.dump(self.data, temporary, indent=2, ensure_ascii=False)
                temporary.write("\n")
                temporary.flush()
                os.fsync(temporary.fileno())
                temporary_path = temporary.name
            os.replace(temporary_path, self.path)
            temporary_path = None
        except OSError:
            return
        finally:
            if temporary_path:
                try:
                    os.unlink(temporary_path)
                except OSError:
                    pass

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value) -> None:
        if key not in self.DEFAULTS:
            return
        if not isinstance(value, type(self.DEFAULTS[key])):
            raise TypeError(f"Invalid value type for setting '{key}'")
        self.data[key] = value

    def add_recent_file(self, path: str) -> None:
        path = str(Path(path).expanduser().resolve())
        files = [item for item in self.data.get("recent_files", []) if item != path and Path(item).exists()]
        self.data["recent_files"] = [path, *files][:10]

    def recent_files(self) -> list[str]:
        files = [path for path in self.data.get("recent_files", []) if Path(path).exists()]
        self.data["recent_files"] = files[:10]
        return list(self.data["recent_files"])
