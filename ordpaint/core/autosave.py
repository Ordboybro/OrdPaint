from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .document import Document
from .project import ProjectError, load_project, save_project


@dataclass
class AutosaveManager:
    """Revision-based crash-recovery layer around the native project serializer."""

    path: Path
    last_revision: int | None = None

    @classmethod
    def for_project(cls, project_path: str | Path) -> "AutosaveManager":
        project = Path(project_path).expanduser()
        return cls(project.with_name(f".{project.name}.autosave"))

    @classmethod
    def for_directory(cls, directory: str | Path, name: str = "untitled") -> "AutosaveManager":
        root = Path(directory).expanduser()
        return cls(root / f".{name}.autosave")

    def needs_autosave(self, document: Document) -> bool:
        return self.last_revision != document.revision

    def autosave(self, document: Document, *, force: bool = False) -> bool:
        if not force and not self.needs_autosave(document):
            return False
        try:
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

    def recover(self) -> Document:
        if not self.has_recovery():
            raise ProjectError("No autosave recovery is available")
        return load_project(self.path)

    def discard(self) -> bool:
        try:
            self.path.unlink()
        except FileNotFoundError:
            return False
        except OSError:
            return False
        self.last_revision = None
        return True
