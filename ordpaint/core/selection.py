from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QPoint, QRect


class SelectionMode(StrEnum):
    REPLACE = "replace"
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"


class Selection:
    """UI-independent rectangular selection model."""

    def __init__(self) -> None:
        self.rect: QRect | None = None

    @property
    def active(self) -> bool:
        return self.rect is not None and not self.rect.isEmpty()

    def clear(self) -> None:
        self.rect = None

    def select_all(self, width: int, height: int) -> None:
        self.rect = QRect(0, 0, max(0, width), max(0, height))

    def set_rect(self, rect: QRect, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        rect = rect.normalized()
        if rect.isEmpty():
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        if not self.active or mode == SelectionMode.REPLACE:
            self.rect = rect
            return
        if mode == SelectionMode.ADD:
            self.rect = self.rect.united(rect)
        elif mode == SelectionMode.INTERSECT:
            intersection = self.rect.intersected(rect)
            self.rect = intersection if not intersection.isEmpty() else None
        elif mode == SelectionMode.SUBTRACT:
            self.rect = self._subtract(self.rect, rect)

    def move(self, dx: int, dy: int, width: int, height: int) -> None:
        if not self.active:
            return
        rect = self.rect.translated(dx, dy)
        max_x = max(0, width - rect.width())
        max_y = max(0, height - rect.height())
        rect.moveTo(max(0, min(rect.x(), max_x)), max(0, min(rect.y(), max_y)))
        self.rect = rect

    def contains(self, point: QPoint) -> bool:
        return self.active and self.rect.contains(point)

    def clamp(self, width: int, height: int) -> None:
        if not self.active:
            return
        clipped = self.rect.intersected(QRect(0, 0, width, height))
        self.rect = clipped if not clipped.isEmpty() else None

    @staticmethod
    def _subtract(source: QRect, cutter: QRect) -> QRect | None:
        intersection = source.intersected(cutter)
        if intersection.isEmpty():
            return source
        if intersection == source:
            return None
        candidates = [
            QRect(source.left(), source.top(), source.width(), intersection.top() - source.top()),
            QRect(source.left(), intersection.bottom() + 1, source.width(), source.bottom() - intersection.bottom()),
            QRect(source.left(), intersection.top(), intersection.left() - source.left(), intersection.height()),
            QRect(intersection.right() + 1, intersection.top(), source.right() - intersection.right(), intersection.height()),
        ]
        candidates = [candidate for candidate in candidates if not candidate.isEmpty()]
        return max(candidates, key=lambda candidate: candidate.width() * candidate.height()) if candidates else None
