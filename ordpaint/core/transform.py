from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QImage, QPainter, QTransform


class TransformHandle(StrEnum):
    MOVE = "move"
    NORTH = "north"
    SOUTH = "south"
    WEST = "west"
    EAST = "east"
    NORTH_WEST = "north_west"
    NORTH_EAST = "north_east"
    SOUTH_WEST = "south_west"
    SOUTH_EAST = "south_east"


@dataclass
class TransformState:
    """UI-independent state for one floating raster transform.

    The document is not mutated while this object is being edited. A UI can
    freely move, resize, flip or rotate the state and commit exactly one final
    operation to history.
    """

    image: QImage
    rect: QRectF
    source_rect: QRect | None = None
    source_layer_index: int | None = None
    create_new_layer: bool = False

    @classmethod
    def from_image(
        cls,
        image: QImage,
        position: QPointF | None = None,
        *,
        source_rect: QRect | None = None,
        source_layer_index: int | None = None,
        create_new_layer: bool = False,
    ) -> "TransformState":
        if image.isNull():
            raise ValueError("Transform image must not be null")
        position = position or QPointF()
        return cls(
            image.copy(),
            QRectF(position.x(), position.y(), image.width(), image.height()),
            QRect(source_rect) if source_rect is not None else None,
            source_layer_index,
            create_new_layer,
        )

    @property
    def active(self) -> bool:
        return not self.image.isNull() and self.rect.width() > 0 and self.rect.height() > 0

    @property
    def aspect_ratio(self) -> float:
        return self.rect.width() / self.rect.height() if self.rect.height() else 1.0

    def copy(self) -> "TransformState":
        return TransformState(
            self.image.copy(),
            QRectF(self.rect),
            QRect(self.source_rect) if self.source_rect is not None else None,
            self.source_layer_index,
            self.create_new_layer,
        )

    def handle_positions(self) -> dict[TransformHandle, QPointF]:
        """Return the eight resize handles plus the centre move handle."""
        return {
            TransformHandle.NORTH_WEST: self.rect.topLeft(),
            TransformHandle.NORTH: QPointF(self.rect.center().x(), self.rect.top()),
            TransformHandle.NORTH_EAST: self.rect.topRight(),
            TransformHandle.EAST: QPointF(self.rect.right(), self.rect.center().y()),
            TransformHandle.SOUTH_EAST: self.rect.bottomRight(),
            TransformHandle.SOUTH: QPointF(self.rect.center().x(), self.rect.bottom()),
            TransformHandle.SOUTH_WEST: self.rect.bottomLeft(),
            TransformHandle.WEST: QPointF(self.rect.left(), self.rect.center().y()),
            TransformHandle.MOVE: self.rect.center(),
        }

    def hit_test(self, point: QPointF, tolerance: float = 6.0) -> TransformHandle | None:
        """Return the handle under *point* in document coordinates."""
        if tolerance < 0:
            raise ValueError("Transform hit tolerance must not be negative")
        tolerance_squared = tolerance * tolerance
        for handle in (
            TransformHandle.NORTH_WEST,
            TransformHandle.NORTH,
            TransformHandle.NORTH_EAST,
            TransformHandle.EAST,
            TransformHandle.SOUTH_EAST,
            TransformHandle.SOUTH,
            TransformHandle.SOUTH_WEST,
            TransformHandle.WEST,
        ):
            position = self.handle_positions()[handle]
            dx = point.x() - position.x()
            dy = point.y() - position.y()
            if dx * dx + dy * dy <= tolerance_squared:
                return handle
        if self.rect.contains(point):
            return TransformHandle.MOVE
        return None

    def move(self, delta: QPointF, bounds: QRectF | None = None) -> None:
        moved = QRectF(self.rect)
        moved.translate(delta)
        self.rect = self._clamp_rect(moved, bounds) if bounds is not None else moved

    def resize(
        self,
        handle: TransformHandle | str,
        delta: QPointF,
        *,
        keep_aspect: bool = False,
        minimum_size: float = 1.0,
        bounds: QRectF | None = None,
    ) -> None:
        handle = TransformHandle(handle)
        rect = QRectF(self.rect)

        left, top, right, bottom = rect.left(), rect.top(), rect.right(), rect.bottom()
        if handle in {TransformHandle.WEST, TransformHandle.NORTH_WEST, TransformHandle.SOUTH_WEST}:
            left += delta.x()
        if handle in {TransformHandle.EAST, TransformHandle.NORTH_EAST, TransformHandle.SOUTH_EAST}:
            right += delta.x()
        if handle in {TransformHandle.NORTH, TransformHandle.NORTH_WEST, TransformHandle.NORTH_EAST}:
            top += delta.y()
        if handle in {TransformHandle.SOUTH, TransformHandle.SOUTH_WEST, TransformHandle.SOUTH_EAST}:
            bottom += delta.y()

        if right - left < minimum_size:
            if handle in {TransformHandle.WEST, TransformHandle.NORTH_WEST, TransformHandle.SOUTH_WEST}:
                left = right - minimum_size
            else:
                right = left + minimum_size
        if bottom - top < minimum_size:
            if handle in {TransformHandle.NORTH, TransformHandle.NORTH_WEST, TransformHandle.NORTH_EAST}:
                top = bottom - minimum_size
            else:
                bottom = top + minimum_size

        result = QRectF(QPointF(left, top), QPointF(right, bottom)).normalized()
        if keep_aspect:
            result = self._with_aspect_ratio(result, handle, minimum_size)
        self.rect = self._clamp_rect(result, bounds) if bounds is not None else result

    def flip_horizontal(self) -> None:
        self.image = self.image.mirrored(True, False)

    def flip_vertical(self) -> None:
        self.image = self.image.mirrored(False, True)

    def rotate_90_clockwise(self) -> None:
        self._rotate_90(-90)

    def rotate_90_counterclockwise(self) -> None:
        self._rotate_90(90)

    def _rotate_90(self, angle: int) -> None:
        centre = self.rect.center()
        self.image = self.image.transformed(QTransform().rotate(angle))
        self.rect = QRectF(
            centre.x() - self.rect.height() / 2,
            centre.y() - self.rect.width() / 2,
            self.rect.height(),
            self.rect.width(),
        )

    def render_on(self, image: QImage, *, clear_source: bool = False) -> QImage:
        """Return a copy of *image* with the transform raster composited onto it."""
        result = image.copy()
        painter = QPainter(result)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        if clear_source and self.source_rect is not None:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(self.source_rect, Qt.GlobalColor.transparent)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
        painter.drawImage(self.rect, self.image)
        painter.end()
        return result

    def to_int_rect(self) -> QRect:
        return self.rect.toAlignedRect()

    def target_size(self) -> QSize:
        return self.to_int_rect().size()

    @staticmethod
    def _clamp_rect(rect: QRectF, bounds: QRectF) -> QRectF:
        if rect.width() > bounds.width():
            rect.setWidth(bounds.width())
        if rect.height() > bounds.height():
            rect.setHeight(bounds.height())
        if rect.left() < bounds.left():
            rect.moveLeft(bounds.left())
        if rect.top() < bounds.top():
            rect.moveTop(bounds.top())
        if rect.right() > bounds.right():
            rect.moveRight(bounds.right())
        if rect.bottom() > bounds.bottom():
            rect.moveBottom(bounds.bottom())
        return rect

    def _with_aspect_ratio(
        self,
        rect: QRectF,
        handle: TransformHandle,
        minimum_size: float,
    ) -> QRectF:
        ratio = max(0.0001, self.aspect_ratio)
        width = max(minimum_size, rect.width())
        height = max(minimum_size, rect.height())

        if abs(width / height - ratio) < 1e-9:
            return rect
        if width / height > ratio:
            height = width / ratio
        else:
            width = height * ratio

        result = QRectF(rect)
        if handle in {TransformHandle.NORTH, TransformHandle.NORTH_WEST, TransformHandle.NORTH_EAST}:
            result.setTop(result.bottom() - height)
        else:
            result.setBottom(result.top() + height)
        if handle in {TransformHandle.WEST, TransformHandle.NORTH_WEST, TransformHandle.SOUTH_WEST}:
            result.setLeft(result.right() - width)
        else:
            result.setRight(result.left() + width)
        return result
