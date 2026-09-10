from __future__ import annotations

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QImage, QPainter, QPixmap, QTransform


def crop_pixmap(pixmap: QPixmap, rect: QRect) -> QPixmap:
    """Return a clipped crop; invalid or empty rectangles produce a null pixmap."""
    bounds = rect.normalized().intersected(QRect(0, 0, pixmap.width(), pixmap.height()))
    return pixmap.copy(bounds) if not bounds.isEmpty() else QPixmap()


def crop_document(document, rect: QRect) -> bool:
    """Crop every layer to the same document rectangle."""
    bounds = rect.normalized().intersected(QRect(0, 0, document.width, document.height))
    if bounds.isEmpty() or bounds.width() == document.width and bounds.height() == document.height:
        return False
    for layer in document.layers:
        layer.pixmap = crop_pixmap(layer.pixmap, bounds)
    document.width = bounds.width()
    document.height = bounds.height()
    document.touch()
    return True


def flip_document(document, *, horizontal: bool = False, vertical: bool = False) -> bool:
    if not horizontal and not vertical:
        return False
    transform = QTransform()
    if horizontal:
        transform.scale(-1, 1)
        transform.translate(-document.width, 0)
    if vertical:
        transform.scale(1, -1)
        transform.translate(0, -document.height)
    for layer in document.layers:
        layer.pixmap = layer.pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
    document.touch()
    return True


def rotate_document(document, angle: float) -> bool:
    angle = float(angle) % 360.0
    if abs(angle) < 1e-9:
        return False
    transform = QTransform().rotate(angle)
    for layer in document.layers:
        layer.pixmap = layer.pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation)
    new_width = max(1, document.layers[0].pixmap.width())
    new_height = max(1, document.layers[0].pixmap.height())
    document.width, document.height = new_width, new_height
    document.touch()
    return True


def grayscale_document(document) -> bool:
    changed = False
    for layer in document.layers:
        image = layer.pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                gray = round(0.299 * pixel.red() + 0.587 * pixel.green() + 0.114 * pixel.blue())
                if (pixel.red(), pixel.green(), pixel.blue()) != (gray, gray, gray):
                    pixel.setRed(gray)
                    pixel.setGreen(gray)
                    pixel.setBlue(gray)
                    image.setPixelColor(x, y, pixel)
                    changed = True
        layer.pixmap = QPixmap.fromImage(image)
    if changed:
        document.touch()
    return changed


def invert_document(document) -> bool:
    changed = False
    for layer in document.layers:
        image = layer.pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                pixel.setRed(255 - pixel.red())
                pixel.setGreen(255 - pixel.green())
                pixel.setBlue(255 - pixel.blue())
                image.setPixelColor(x, y, pixel)
                changed = True
        layer.pixmap = QPixmap.fromImage(image)
    if changed:
        document.touch()
    return changed
