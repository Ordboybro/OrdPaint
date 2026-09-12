from __future__ import annotations

from enum import StrEnum

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QImage, QPainter, QPolygon


class SelectionMode(StrEnum):
    REPLACE = "replace"
    ADD = "add"
    SUBTRACT = "subtract"
    INTERSECT = "intersect"


class Selection:
    """Pixel-accurate selection model with a document-sized alpha mask."""

    def __init__(self, width: int = 1, height: int = 1) -> None:
        self._width = max(1, int(width))
        self._height = max(1, int(height))
        self._document_bound = False
        self._mask = QImage(self._width, self._height, QImage.Format.Format_Alpha8)
        self._mask.fill(0)
        self._bounds = QRect()

    @property
    def active(self) -> bool:
        return not self._bounds.isEmpty()

    @property
    def rect(self) -> QRect | None:
        return QRect(self._bounds) if self.active else None

    @rect.setter
    def rect(self, value: QRect | None) -> None:
        if value is None:
            self.clear()
            return
        target = QRect(value).normalized()
        if not self.active:
            self.set_rect(target)
            return
        current = self._bounds.topLeft()
        self.move(target.left() - current.x(), target.top() - current.y())

    @property
    def mask(self) -> QImage:
        return self._mask.copy()

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def set_document_size(self, width: int, height: int) -> None:
        width = max(1, int(width))
        height = max(1, int(height))
        self._document_bound = True
        if (width, height) == (self._width, self._height):
            return
        self._width, self._height = width, height
        self._mask = QImage(width, height, QImage.Format.Format_Alpha8)
        self._mask.fill(0)
        self._bounds = QRect()

    def clear(self) -> None:
        self._mask.fill(0)
        self._bounds = QRect()

    def select_all(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None and height is not None:
            self.set_document_size(width, height)
        self._mask.fill(255)
        self._bounds = QRect(0, 0, self._width, self._height)

    def copy(self) -> "Selection":
        result = Selection(self._width, self._height)
        result._document_bound = self._document_bound
        result._mask = self._mask.copy()
        result._bounds = QRect(self._bounds)
        return result

    def set_rect(self, rect: QRect, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_geometry(rect, "rect", mode)

    def set_ellipse(self, rect: QRect, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_geometry(rect, "ellipse", mode)

    def set_polygon(self, points: list[QPoint], mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_polygon(points, mode)

    def set_lasso(self, points: list[QPoint], mode: SelectionMode = SelectionMode.REPLACE) -> None:
        self._combine_polygon(points, mode)

    def combine_mask(self, mask: QImage, mode: SelectionMode = SelectionMode.REPLACE) -> None:
        if mask.size() != self._mask.size():
            raise ValueError("Selection mask dimensions must match the document")
        source = mask.convertToFormat(QImage.Format.Format_Alpha8)
        self._combine(source, mode, self._nonzero_bounds(source))

    def move(self, dx: int, dy: int, width: int | None = None, height: int | None = None) -> None:
        if width is not None and height is not None:
            self._resize_preserve(width, height, document_bound=True)
        if not self.active:
            return
        dx = int(dx)
        dy = int(dy)
        old_bounds = QRect(self._bounds)
        if self._document_bound:
            dx = max(-old_bounds.left(), min(dx, self._width - old_bounds.right() - 1))
            dy = max(-old_bounds.top(), min(dy, self._height - old_bounds.bottom() - 1))
        if dx == 0 and dy == 0:
            return
        moved = QImage(self._width, self._height, QImage.Format.Format_Alpha8)
        moved.fill(0)
        painter = QPainter(moved)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(dx, dy, self._mask)
        painter.end()
        self._mask = moved
        self._bounds = old_bounds.translated(dx, dy).intersected(self._mask.rect())

    def contains(self, point: QPoint) -> bool:
        return self.coverage(point) > 0

    def coverage(self, point: QPoint) -> int:
        if not self._bounds.contains(point):
            return 0
        return self._mask.pixelColor(point).alpha()

    def bounding_rect(self) -> QRect:
        return QRect(self._bounds)

    def clamp(self, width: int, height: int) -> None:
        self._resize_preserve(width, height, document_bound=True)
        if self._bounds.isEmpty():
            return
        self._bounds = self._bounds.intersected(self._mask.rect())
        if self._bounds.isEmpty():
            self.clear()

    def _resize_preserve(self, width: int, height: int, *, document_bound: bool) -> None:
        width = max(1, int(width))
        height = max(1, int(height))
        if document_bound:
            self._document_bound = True
        if (width, height) == (self._width, self._height):
            return
        old = self._mask
        self._width, self._height = width, height
        self._mask = QImage(width, height, QImage.Format.Format_Alpha8)
        self._mask.fill(0)
        painter = QPainter(self._mask)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Source)
        painter.drawImage(0, 0, old)
        painter.end()
        self._bounds = self._bounds.intersected(self._mask.rect())

    def _ensure_capacity(self, width: int, height: int) -> None:
        if self._document_bound or width <= self._width and height <= self._height:
            return
        self._resize_preserve(width, height, document_bound=False)

    @staticmethod
    def _shape_image(width: int, height: int, rect: QRect, shape: str) -> QImage:
        source = QImage(width, height, QImage.Format.Format_Alpha8)
        source.fill(0)
        painter = QPainter(source)
        brush = QColor(255, 255, 255, 255)
        painter.setPen(brush)
        painter.setBrush(brush)
        if shape == "ellipse":
            painter.drawEllipse(rect)
        else:
            painter.fillRect(rect, brush)
        painter.end()
        return source

    def _combine_geometry(self, rect: QRect, shape: str, mode: SelectionMode) -> None:
        rect = rect.normalized()
        if not self._document_bound:
            self._ensure_capacity(max(1, rect.right() + 1), max(1, rect.bottom() + 1))
        normalized = rect.intersected(self._mask.rect())
        if normalized.isEmpty():
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        source = self._shape_image(self._width, self._height, normalized, shape)
        self._combine(source, mode, normalized)

    def _combine_polygon(self, points: list[QPoint], mode: SelectionMode) -> None:
        if len(points) < 3:
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        polygon = QPolygon(points)
        if not self._document_bound:
            bounds = polygon.boundingRect()
            self._ensure_capacity(max(1, bounds.right() + 1), max(1, bounds.bottom() + 1))
        bounds = polygon.boundingRect().intersected(self._mask.rect())
        if bounds.isEmpty():
            if mode == SelectionMode.REPLACE:
                self.clear()
            return
        source = QImage(self._width, self._height, QImage.Format.Format_Alpha8)
        source.fill(0)
        painter = QPainter(source)
        brush = QColor(255, 255, 255, 255)
        painter.setPen(brush)
        painter.setBrush(brush)
        painter.drawPolygon(polygon)
        painter.end()
        self._combine(source, mode, bounds)

    def _combine(self, source: QImage, mode: SelectionMode, source_bounds: QRect) -> None:
        mode = SelectionMode(mode)
        if mode == SelectionMode.REPLACE:
            self._mask = source.copy()
        else:
            painter = QPainter(self._mask)
            composition = {
                SelectionMode.ADD: QPainter.CompositionMode.CompositionMode_SourceOver,
                SelectionMode.SUBTRACT: QPainter.CompositionMode.CompositionMode_DestinationOut,
                SelectionMode.INTERSECT: QPainter.CompositionMode.CompositionMode_DestinationIn,
            }[mode]
            painter.setCompositionMode(composition)
            painter.drawImage(0, 0, source)
            painter.end()

        if mode == SelectionMode.REPLACE:
            self._bounds = QRect(source_bounds).intersected(self._mask.rect())
        elif mode == SelectionMode.SUBTRACT:
            self._bounds = self._nonzero_bounds(self._mask)
        elif mode == SelectionMode.INTERSECT:
            self._bounds = self._nonzero_bounds(self._mask, self._bounds.intersected(source_bounds))
        else:
            current = QRect(self._bounds)
            self._bounds = current.united(source_bounds).intersected(self._mask.rect()) if not current.isEmpty() else QRect(source_bounds).intersected(self._mask.rect())

    @staticmethod
    def _nonzero_bounds(image: QImage, region: QRect | None = None) -> QRect:
        area = image.rect() if region is None else region.intersected(image.rect())
        if area.isEmpty():
            return QRect()
        left, top = area.right(), area.bottom()
        right, bottom = -1, -1
        for y in range(area.top(), area.bottom() + 1):
            for x in range(area.left(), area.right() + 1):
                if image.pixelColor(x, y).alpha() > 0:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)
        return QRect(QPoint(left, top), QPoint(right, bottom)) if right >= left and bottom >= top else QRect()
