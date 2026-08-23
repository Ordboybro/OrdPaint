from __future__ import annotations

from dataclasses import dataclass

from .document import Document


@dataclass(frozen=True)
class HistoryState:
    document: Document
    serial: int


class History:
    """Snapshot history for complete user-level document actions.

    Call ``push`` immediately before a mutating action. The snapshot is the
    exact state restored by Undo. The serial cursor also lets the UI determine
    whether the current document differs from the last saved state.
    """

    def __init__(self, limit: int = 50) -> None:
        self.limit = max(1, int(limit))
        self._undo: list[HistoryState] = []
        self._redo: list[HistoryState] = []
        self._serial = 0
        self._saved_serial = 0

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._serial = 0
        self._saved_serial = 0

    def push(self, document: Document) -> None:
        self._serial += 1
        self._undo.append(HistoryState(document.copy(), self._serial))
        if len(self._undo) > self.limit:
            del self._undo[: len(self._undo) - self.limit]
        self._redo.clear()

    def mark_saved(self) -> None:
        """Mark the current history position as the last persisted state."""
        self._saved_serial = self._serial

    def is_dirty(self) -> bool:
        return self._serial != self._saved_serial

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self, current: Document) -> Document | None:
        if not self._undo:
            return None
        self._redo.append(HistoryState(current.copy(), self._serial))
        state = self._undo.pop()
        self._serial = state.serial - 1
        return state.document.copy()

    def redo(self, current: Document) -> Document | None:
        if not self._redo:
            return None
        self._undo.append(HistoryState(current.copy(), self._serial))
        state = self._redo.pop()
        self._serial = state.serial
        return state.document.copy()

    def __len__(self) -> int:
        return len(self._undo)
