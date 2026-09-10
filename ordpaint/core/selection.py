from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QImage, QPainter, QPolygon


class SelectionMode(StrEnum):
    REPLACE = "replace"
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"


class Selection:
    """Pixel-accurate selection model with rectangle, ellipse, polygon and lasso support.

    ``rect`` remains available for compatibility and always exposes the mask's
    bounding rectangle. Editing code can use ``mask``/``contains`` for exact
    pixel clipping.
    """

    def __init__(self, width: int = 1, height: int = 1) -> None:
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self._mask = QImage(self._width, self._height, QImage.Format.Format_Grayscale8)
        self._mask.fill(0)

    @property
    def active(self) -> bool:
        return not self._mask.isNull() and not self._mask.isAllGray() if False else not self.bounding_rect().isEmpty()

    @property
    def rect(self) -> QRect | None:
        bounds = self.bounding_rect()
        return bounds if not bounds.isEmpty() else None

    @property
    def mask(self) -> QImage:
        """Return a defensive copy of the 8-bit mask."""
        return self._mask.copy()

    def set_document_size(self, width: int, height: int) -> None:
        width = max(1, int(width))
        height = max(1, int(height))
        if (width, height) == (self._width, self._height):
            return
        self._width, self._height = width, height
        self._mask = QImage(width, height, QImage.Format.Format_Grayscale8)
        self._mask.fill(0)

    def clear(self) -> None:
        self._mask.fill(0)

    def select_all(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None and height is not None:
            self.set_document_size(width, height)
        self._mask.fill(255)

    def copy(self) -> "Selection":
        result = Selection(self._width, self._height)
        result._mask = self._mask.copy()
        return result

    def set_rect(self, rect: QRect, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_geometry(rect, "rect", mode)

    def set_ellipse(self, rect: QRect, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_geometry(rect, "ellipse", mode)

    def set_polygon(self, points: list[QPoint], mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_polygon(points, mode)

    def set_lasso(self, points: list[QPoint], mode: SelectionMode = SelectionMode.REPLACE) -> None:
        """Create a freehand lasso selection from a sampled closed path."""
        self._combine_polygon(points, mode)

    def combine_mask(self, mask: QImage, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        if mask.size() != self._mask.size():
            raise ValueError("Selection mask dimensions must match the document")
        source = mask.convertToFormat(QImage.Format.Format_Grayscale8)
        self._combine(source, mode)

    def move(self, dx: int, dy: int, width: int | None = None, height: int | None = None) -> None:
        if width is not None and height is not None:
            self.set_document_size(width, height)
        if not self.active:
            return
        moved = QImage(self._width, self._height, QImage.Format.Format_Grayscale8)
        moved.fill(0)
        painter = QPainter(moved)
        painter.drawImage(int(dx), int(dy), self._mask)
        painter.end()
        self._mask = moved

    def contains(self, point: QPoint) -> bool:
        if not self._mask.rect().contains(point):
            return False
        return self._mask.pixelColor(point).value() > 0

    def coverage(self, point: QPoint) -> int:
        if not self._mask.rect().contains(point):
            return 0
        return self._mask.pixelColor(point).value()

    def bounding_rect(self) -> QRect:
        return self._mask.boundingRect() if self._mask.isNull() is False else QRect()

    def clamp(self, width: int, height: int) -> None:
        self.set_document_size(width, height)

    def _combine_geometry(self, rect: QRect, shape: str, mode: SelectionMode) -> None:
        normalized = rect.normalized().intersected(self._mask.rect())
        source = QImage(self._width, self._height, QImage.Format.Format_Grayscale8)
        source.fill(0)
        if normalized.isEmpty():
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        painter = QPainter(source)
        painter.setPen(255)
        painter.setBrush(255)
        if shape == "ellipse":
            painter.drawEllipse(normalized)
        else:
            painter.drawRect(normalized)
        painter.end()
        self._combine(source, mode)

    def _combine_polygon(self, points: list[QPoint], mode: SelectionMode) -> None:
        if len(points) < 3:
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        source = QImage(self._width, self._height, QImage.Format.Format_Grayscale8)
        source.fill(0)
        painter = QPainter(source)
        painter.setPen(255)
        painter.setBrush(255)
        painter.drawPolygon(QPolygon(points))
        painter.end()
        self._combine(source, mode)

    def _combine(self, source: QImage, mode: SelectionMode) -> None:
        modes = {
            SelectionMode.REPLACE: QPainter.CompositionMode.CompositionMode_Source,
            SelectionMode.ADD: QPainter.CompositionMode.CompositionMode_SourceOver,
            SelectionMode.SUBTRACT: QPainter.CompositionMode.CompositionMode_DestinationOut,
            SelectionMode.INTERSECT: QPainter.CompositionMode.CompositionMode_DestinationIn,
        }
        painter = QPainter(self._mask)
        painter.setCompositionMode(modes[SelectionMode(mode)])
        painter.drawImage(0, 0, source)
        painter.end()

    def to_dict(self) -> dict[str, object]:
        """Small serializable selection descriptor for session metadata."""
        return {"width": self._width, "height": self._height, "active": self.active}
