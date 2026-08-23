from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPixmap

from ordpaint.core.clipboard import crop_image, from_pixmap


def test_clipboard_item_copies_pixmap_and_metadata(qt_app):
    pixmap = QPixmap(8, 6)
    pixmap.fill(Qt.GlobalColor.transparent)
    pixmap.setMask(pixmap.createMaskFromColor(QColor("transparent")))
    item = from_pixmap(pixmap, QRect(1, 2, 4, 3), suggested_position=QPoint(5, 7), name="Selection")

    assert item.size.width() == 8
    assert item.size.height() == 6
    assert item.source_rect == QRect(1, 2, 4, 3)
    assert item.suggested_position == QPoint(5, 7)
    assert item.name == "Selection"
    assert item.copy_image().size() == pixmap.size()


def test_crop_image_clips_to_bounds(qt_app):
    image = QImage(10, 10, QImage.Format.Format_ARGB32)
    image.fill(Qt.GlobalColor.red)

    cropped = crop_image(image, QRect(-3, -2, 6, 7))
    assert cropped.size().width() == 3
    assert cropped.size().height() == 5
    assert cropped.pixelColor(0, 0).red() == 255


def test_crop_empty_rect_returns_null_image(qt_app):
    image = QImage(10, 10, QImage.Format.Format_ARGB32)
    assert crop_image(image, QRect(20, 20, 2, 2)).isNull()
