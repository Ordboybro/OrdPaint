from __future__ import annotations

from dataclasses import dataclass

from .document import Document


@dataclass(frozen=True)
class HistoryState:
    document: Document
    state_id: int
    after_id: int


class History:
    """Bounded snapshot history with transactional user actions and a memory budget."""

    def __init__(self, limit: int = 100, memory_limit_mb: int = 512) -> None:
        self.limit = max(1, int(limit))
        self.memory_limit_bytes = max(64, int(memory_limit_mb)) * 1024 * 1024
        self._undo: list[HistoryState] = []
        self._redo: list[HistoryState] = []
        self._undo_bytes = 0
        self._redo_bytes = 0
        self._next_id = 1
        self._current_id = 0
        self._saved_id = 0
        self._transaction: Document | None = None
        self._transaction_revision = -1

    @staticmethod
    def _estimate_bytes(document: Document) -> int:
        pixels = max(1, document.width * document.height)
        return pixels * 4 * max(1, len(document.layers))

    def clear(self) -> None:
        self._undo.clear()
        self._redo.clear()
        self._undo_bytes = 0
        self._redo_bytes = 0
        self._next_id = 1
        self._current_id = 0
        self._saved_id = 0
        self.cancel_transaction()

    def _trim_undo(self) -> None:
        while len(self._undo) > self.limit or (len(self._undo) > 1 and self._undo_bytes > self.memory_limit_bytes):
            state = self._undo.pop(0)
            self._undo_bytes -= self._estimate_bytes(state.document)

    def _push_snapshot(self, document: Document) -> None:
        after_id = self._next_id
        self._next_id += 1
        snapshot = document.copy()
        self._undo.append(HistoryState(snapshot, self._current_id, after_id))
        self._undo_bytes += self._estimate_bytes(snapshot)
        self._current_id = after_id
        self._trim_undo()
        self._redo.clear()
        self._redo_bytes = 0

    def push(self, document: Document) -> None:
        if self._transaction is None:
            self._push_snapshot(document)

    def begin_transaction(self, document: Document) -> bool:
        if self._transaction is not None:
            return False
        self._transaction = document.copy()
        self._transaction_revision = document.revision
        return True

    def end_transaction(self, document: Document) -> bool:
        if self._transaction is None:
            return False
        before = self._transaction
        changed = document.revision != self._transaction_revision
        self.cancel_transaction()
        if not changed:
            return False
        self._push_snapshot(before)
        return True

    def cancel_transaction(self) -> None:
        self._transaction = None
        self._transaction_revision = -1

    def transaction_active(self) -> bool:
        return self._transaction is not None

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
        self.cancel_transaction()
        state = self._undo.pop()
        state_bytes = self._estimate_bytes(state.document)
        self._undo_bytes -= state_bytes
        current_copy = current.copy()
        self._redo.append(HistoryState(current_copy, self._current_id, state.after_id))
        self._redo_bytes += self._estimate_bytes(current_copy)
        self._current_id = state.state_id
        return state.document.copy()

    def redo(self, current: Document) -> Document | None:
        if not self._redo:
            return None
        self.cancel_transaction()
        state = self._redo.pop()
        self._redo_bytes -= self._estimate_bytes(state.document)
        current_copy = current.copy()
        self._undo.append(HistoryState(current_copy, self._current_id, state.after_id))
        self._undo_bytes += self._estimate_bytes(current_copy)
        self._trim_undo()
        self._current_id = state.after_id
        return state.document.copy()

    @property
    def memory_usage_bytes(self) -> int:
        return self._undo_bytes + self._redo_bytes

    def __len__(self) -> int:
        return len(self._undo)
