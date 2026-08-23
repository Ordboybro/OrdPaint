from __future__ import annotations

from dataclasses import dataclass

from .document import Document


@dataclass
class HistoryState:
    document: Document


class History:
    def __init__(self, limit: int = 50) -> None:
        self.limit = max(1, limit)
        self._undo: list[HistoryState] = []
        self._redo: list[HistoryState] = []

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()

    def push(self, document: Document) -> None:
        self._undo.append(HistoryState(document.copy()))
        if len(self._undo) > self.limit:
            self._undo.pop(0)
        self._redo.clear()

    def can_undo(self) -> bool:
        return bool(self._undo)

    def can_redo(self) -> bool:
        return bool(self._redo)

    def undo(self, current: Document) -> Document | None:
        if not self._undo:
            return None
        self._redo.append(HistoryState(current.copy()))
        return self._undo.pop().document.copy()

    def redo(self, current: Document) -> Document | None:
        if not self._redo:
            return None
        self._undo.append(HistoryState(current.copy()))
        return self._redo.pop().document.copy()
