from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPixmap

from ordpaint.core.raster import clear_rect, draw_line, extract, flood_fill, paste


def test_draw_line_and_clear(qt_app):
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.GlobalColor.transparent)
    draw_line(pixmap, QPoint(2, 2), QPoint(17, 17), QColor("red"), 3)
    assert pixmap.toImage().pixelColor(10, 10).red() == 255
    clear_rect(pixmap, QRect(8, 8, 5, 5))
    assert pixmap.toImage().pixelColor(10, 10).alpha() == 0


def test_flood_fill_changes_region(qt_app):
    pixmap = QPixmap(8, 8)
    pixmap.fill(Qt.GlobalColor.white)
    changed = flood_fill(pixmap, QPoint(2, 2), QColor("blue"))
    assert changed
    assert pixmap.toImage().pixelColor(2, 2).blue() == 255


def test_flood_fill_respects_clip(qt_app):
    pixmap = QPixmap(10, 10)
    pixmap.fill(Qt.GlobalColor.white)
    changed = flood_fill(pixmap, QPoint(2, 2), QColor("blue"), clip=QRect(0, 0, 4, 10))
    assert changed
    image = pixmap.toImage()
    assert image.pixelColor(2, 2).blue() == 255
    assert image.pixelColor(5, 2).red() == 255


def test_flood_fill_tolerance_crosses_similar_colors(qt_app):
    pixmap = QPixmap(3, 1)
    pixmap.fill(Qt.GlobalColor.transparent)
    image = pixmap.toImage()
    image.setPixelColor(0, 0, QColor(100, 100, 100))
    image.setPixelColor(1, 0, QColor(104, 100, 100))
    image.setPixelColor(2, 0, QColor(120, 100, 100))
    pixmap = QPixmap.fromImage(image)

    changed = flood_fill(pixmap, QPoint(0, 0), QColor("blue"), tolerance=5)

    assert changed
    result = pixmap.toImage()
    assert result.pixelColor(0, 0).blue() == 255
    assert result.pixelColor(1, 0).blue() == 255
    assert result.pixelColor(2, 0).red() == 120


def test_extract_and_paste(qt_app):
    source = QPixmap(10, 10)
    source.fill(Qt.GlobalColor.red)
    piece = extract(source, QRect(2, 2, 4, 4))
    target = QPixmap(12, 12)
    target.fill(Qt.GlobalColor.transparent)
    paste(target, piece, QPoint(5, 5))
    assert target.toImage().pixelColor(6, 6).red() == 255
