from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RecentFiles:
    """Portable recent-project list with normalization and duplicate removal."""

    max_items: int = 10
    paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.max_items = max(1, int(self.max_items))
        initial = list(self.paths)
        self.paths.clear()
        for path in reversed(initial):
            self.add(path)

    @staticmethod
    def normalize(path: str | Path) -> str:
        return str(Path(path).expanduser().resolve(strict=False))

    def add(self, path: str | Path) -> None:
        value = self.normalize(path)
        self.paths = [item for item in self.paths if item != value]
        self.paths.insert(0, value)
        del self.paths[self.max_items :]

    def remove(self, path: str | Path) -> bool:
        value = self.normalize(path)
        try:
            self.paths.remove(value)
        except ValueError:
            return False
        return True

    def clear(self) -> None:
        self.paths.clear()

    def existing(self) -> list[str]:
        return [path for path in self.paths if Path(path).is_file()]

    def to_list(self) -> list[str]:
        return list(self.paths)

    @classmethod
    def from_list(cls, paths: list[str] | tuple[str, ...], max_items: int = 10) -> "RecentFiles":
        return cls(max_items=max_items, paths=list(paths))
