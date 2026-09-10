from __future__ import annotations

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QBrush, QImage, QPainter, QPolygon


class SelectionMask:
    """Pixel-accurate 8-bit selection mask used by advanced selection tools."""

    def __init__(self, width: int, height: int) -> None:
        if width < 1 or height < 1:
            raise ValueError("Selection dimensions must be positive")
        self.image = QImage(width, height, QImage.Format.Format_Grayscale8)
        self.clear()

    @property
    def width(self) -> int:
        return self.image.width()

    @property
    def height(self) -> int:
        return self.image.height()

    def clear(self) -> None:
        self.image.fill(0)

    def select_all(self) -> None:
        self.image.fill(255)

    def copy(self) -> "SelectionMask":
        result = SelectionMask(self.width, self.height)
        result.image = self.image.copy()
        return result

    def set_rect(self, rect: QRect) -> None:
        self._paint_geometry(rect, ellipse=False)

    def set_ellipse(self, rect: QRect) -> None:
        self._paint_geometry(rect, ellipse=True)

    def set_polygon(self, points: list[QPoint]) -> None:
        self.clear()
        if len(points) < 3:
            return
        painter = QPainter(self.image)
        painter.setBrush(QBrush(255))
        painter.setPen(QBrush(255).color())
        painter.drawPolygon(QPolygon(points))
        painter.end()

    def combine(self, other: "SelectionMask", mode: str = "replace") -> None:
        if (self.width, self.height) != (other.width, other.height):
            raise ValueError("Selection masks must have equal dimensions")
        modes = {
            "replace": QPainter.CompositionMode.CompositionMode_Source,
            "add": QPainter.CompositionMode.CompositionMode_SourceOver,
            "subtract": QPainter.CompositionMode.CompositionMode_DestinationOut,
            "intersect": QPainter.CompositionMode.CompositionMode_DestinationIn,
        }
        if mode not in modes:
            raise ValueError(f"Unknown selection mode: {mode}")
        painter = QPainter(self.image)
        painter.setCompositionMode(modes[mode])
        painter.drawImage(0, 0, other.image)
        painter.end()

    def contains(self, point: QPoint) -> bool:
        return self.image.rect().contains(point) and self.image.pixelColor(point).value() > 0

    def bounding_rect(self) -> QRect:
        left = self.width
        top = self.height
        right = bottom = -1
        for y in range(self.height):
            for x in range(self.width):
                if self.image.pixelColor(x, y).value() > 0:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)
        if right < 0:
            return QRect()
        return QRect(QPoint(left, top), QPoint(right, bottom))

    def _paint_geometry(self, rect: QRect, *, ellipse: bool) -> None:
        self.clear()
        normalized = rect.normalized().intersected(self.image.rect())
        if normalized.isEmpty():
            return
        painter = QPainter(self.image)
        painter.setBrush(QBrush(255))
        painter.setPen(QBrush(255).color())
        if ellipse:
            painter.drawEllipse(normalized)
        else:
            painter.drawRect(normalized)
        painter.end()
