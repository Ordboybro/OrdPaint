from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .autosave import AutosaveManager
from .document import Document
from .project import ProjectError
from .recent import RecentFiles


@dataclass
class SessionManager:
    """UI-agnostic application session state.

    Keeps recent projects and the current autosave target in one small object so
    the Qt layer only has to schedule timer ticks and persist plain settings.
    """

    recent: RecentFiles = field(default_factory=RecentFiles)
    autosave_directory: Path = field(default_factory=lambda: Path.home() / ".ordpaint")
    autosave_name: str = "untitled"
    project_path: Path | None = None
    autosave: AutosaveManager = field(init=False)

    def __post_init__(self) -> None:
        self.autosave_directory = Path(self.autosave_directory).expanduser()
        self.autosave = AutosaveManager.for_directory(self.autosave_directory, self.autosave_name)

    @property
    def recovery_path(self) -> Path:
        return self.autosave.path

    def set_project(self, path: str | Path | None) -> None:
        self.project_path = Path(path).expanduser() if path else None
        if self.project_path is None:
            self.autosave = AutosaveManager.for_directory(self.autosave_directory, self.autosave_name)
            return
        self.recent.add(self.project_path)
        self.autosave = AutosaveManager.for_project(self.project_path)

    def has_recovery(self) -> bool:
        return self.autosave.has_recovery()

    def recover_document(self) -> Document:
        return self.autosave.recover()

    def discard_recovery(self) -> bool:
        return self.autosave.discard()

    def tick_autosave(self, document: Document) -> bool:
        try:
            self.autosave.path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            return False
        return self.autosave.autosave(document)

    def clear_recovery(self) -> bool:
        return self.discard_recovery()

    def serialize_recent(self) -> list[str]:
        return self.recent.to_list()

    def restore_recent(self, paths: list[str]) -> None:
        self.recent = RecentFiles.from_list(paths, max_items=self.recent.max_items)

    def recover_or_none(self) -> Document | None:
        """Return a recovered document without making startup crash on bad data."""
        if not self.has_recovery():
            return None
        try:
            return self.recover_document()
        except (OSError, ProjectError):
            return None
