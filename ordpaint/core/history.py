from __future__ import annotations

from dataclasses import dataclass

from .document import Document


@dataclass(frozen=True)
class HistoryState:
    """A reversible transition: document before an action and its state id."""

    document: Document
    state_id: int
    after_id: int


class History:
    """Snapshot history for complete user-level document actions.

    ``push`` must be called immediately before a mutating action. Each push
    creates a unique state id, so dirty tracking remains correct even after
    undoing and then making a new change (history branching).
    """

    def __init__(self, limit: int = 50) -> None:
        self.limit = max(1, int(limit))
        self._undo: list[HistoryState] = []
        self._redo: list[HistoryState] = []
        self._next_id = 1
        self._current_id = 0
        self._saved_id = 0

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._next_id = 1
        self._current_id = 0
        self._saved_id = 0

    def push(self, document: Document) -> None:
        after_id = self._next_id
        self._next_id += 1
        self._undo.append(HistoryState(document.copy(), self._current_id, after_id))
        self._current_id = after_id
        if len(self._undo) > self.limit:
            del self._undo[: len(self._undo) - self.limit]
        self._redo.clear()

    def mark_saved(self) -> None:
        self._saved_id = self._current_id

    def is_dirty(self) -> bool:
        return self._current_id != self._saved_id

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self, current: Document) -> Document | None:
        if not self._undo:
            return None
        state = self._undo.pop()
        self._redo.append(HistoryState(current.copy(), self._current_id, state.after_id))
        self._current_id = state.state_id
        return state.document.copy()

    def redo(self, current: Document) -> Document | None:
        if not self._redo:
            return None
        state = self._redo.pop()
        self._undo.append(HistoryState(current.copy(), self._current_id, state.after_id))
        self._current_id = state.after_id
        return state.document.copy()

    def __len__(self) -> int:
        return len(self._undo)
