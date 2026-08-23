from __future__ import annotations

from PySide6.QtCore import QPoint, QRect


class Selection:
    """Small, UI-independent rectangular selection model."""

    def __init__(self) -> None:
        self.rect: QRect | None = None

    @property
    def active(self) -> bool:
        return self.rect is not None and not self.rect.isEmpty()

    def clear(self) -> None:
        self.rect = None

    def select_all(self, width: int, height: int) -> None:
        self.rect = QRect(0, 0, max(0, width), max(0, height))

    def set_rect(self, rect: QRect) -> None:
        self.rect = rect.normalized() if not rect.isEmpty() else None

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
