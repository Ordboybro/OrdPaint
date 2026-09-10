from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .document import Document
from .project import ProjectError, load_project, save_project


@dataclass
class AutosaveManager:
    """Revision-based crash recovery with a small rotating history of snapshots."""

    path: Path
    last_revision: int | None = None
    max_versions: int = 3

    @classmethod
    def for_project(cls, project_path: str | Path) -> "AutosaveManager":
        project = Path(project_path).expanduser()
        return cls(project.with_name(f".{project.name}.autosave"))

    @classmethod
    def for_directory(cls, directory: str | Path, name: str = "untitled") -> "AutosaveManager":
        root = Path(directory).expanduser()
        return cls(root / f".{name}.autosave")

    def _version_path(self, index: int) -> Path:
        return self.path.with_name(f"{self.path.name}.{index}")

    def needs_autosave(self, document: Document) -> bool:
        return self.last_revision != document.revision

    def autosave(self, document: Document, *, force: bool = False) -> bool:
        if not force and not self.needs_autosave(document):
            return False
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            for index in range(self.max_versions - 1, 0, -1):
                source = self._version_path(index - 1) if index > 1 else self.path
                target = self._version_path(index)
                if source.exists():
                    source.replace(target)
            save_project(document, self.path)
        except (OSError, ProjectError):
            return False
        self.last_revision = document.revision
        return True

    def has_recovery(self) -> bool:
        try:
            return self.path.is_file() and self.path.stat().st_size > 0
        except OSError:
            return False

    def recovery_versions(self) -> list[Path]:
        candidates = [self.path] + [self._version_path(i) for i in range(1, self.max_versions)]
        result = []
        for path in candidates:
            try:
                if path.is_file() and path.stat().st_size > 0:
                    result.append(path)
            except OSError:
                continue
        return result

    def recover(self, path: str | Path | None = None) -> Document:
        source = Path(path).expanduser() if path else self.path
        if not source.is_file():
            raise ProjectError("No autosave recovery is available")
        return load_project(source)

    def discard(self) -> bool:
        removed = False
        for path in [self.path] + [self._version_path(i) for i in range(1, self.max_versions)]:
            try:
                path.unlink()
                removed = True
            except FileNotFoundError:
                pass
            except OSError:
                return removed
        self.last_revision = None
        return removed
