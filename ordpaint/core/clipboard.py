from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QImage, QPixmap


@dataclass(frozen=True)
class ClipboardItem:
    """Portable raster payload used by copy/cut/paste operations."""

    image: QImage
    source_rect: QRect | None = None
    suggested_position: QPoint = QPoint()
    name: str = "Pasted"

    def copy_image(self) -> QImage:
        return self.image.copy()

    @property
    def size(self):
        return self.image.size()


def from_pixmap(
    pixmap: QPixmap,
    source_rect: QRect | None = None,
    *,
    suggested_position: QPoint = QPoint(),
    name: str = "Pasted",
) -> ClipboardItem:
    if pixmap.isNull():
        raise ValueError("Cannot copy a null pixmap")
    return ClipboardItem(
        image=pixmap.toImage().copy(),
        source_rect=QRect(source_rect) if source_rect is not None else None,
        suggested_position=QPoint(suggested_position),
        name=name,
    )


def crop_image(image: QImage, rect: QRect) -> QImage:
    if image.isNull():
        return QImage()
    bounds = QRect(0, 0, image.width(), image.height())
    clipped = rect.normalized().intersected(bounds)
    if clipped.isEmpty():
        return QImage()
    return image.copy(clipped)
