from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QGuiApplication

from ordpaint.core.document import Document
from ordpaint.ui.canvas import Canvas


def test_canvas_selection_clips_drawing(qt_app):
    document = Document(20, 20)
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(5, 5, 5, 5))
    canvas.set_color(QColor("red"))
    canvas.brush_size = 1
    canvas._draw_segment(QPoint(0, 7), QPoint(19, 7))

    image = document.active_layer.pixmap.toImage()
    assert image.pixelColor(2, 7).alpha() == 0
    assert image.pixelColor(7, 7).red() == 255
    assert image.pixelColor(12, 7).alpha() == 0


def test_canvas_flood_fill_respects_selection(qt_app):
    document = Document(10, 10)
    document.active_layer.pixmap.fill(QColor("white"))
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(2, 2, 4, 4))
    canvas.set_color(QColor("red"))
    canvas._flood_fill(QPoint(3, 3))

    image = document.active_layer.pixmap.toImage()
    assert image.pixelColor(3, 3).red() == 255
    assert image.pixelColor(0, 0).red() == 255 and image.pixelColor(0, 0).green() == 255


def test_canvas_clipboard_copy_and_paste(qt_app):
    clipboard = QGuiApplication.clipboard()
    clipboard.clear()
    document = Document(12, 12)
    document.active_layer.pixmap.fill(QColor("blue"))
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(2, 2, 3, 3))

    assert canvas.copy_selection() is True
    assert clipboard.mimeData().hasImage()
    assert canvas.paste_from_clipboard() is True
    assert len(document.layers) == 2
    assert document.active_layer.pixmap.toImage().pixelColor(2, 2).blue() == 255


def test_canvas_zoom_limits(qt_app):
    canvas = Canvas(Document(100, 100))
    canvas.set_zoom(100)
    assert canvas.zoom == canvas.MAX_ZOOM
    canvas.set_zoom(0)
    assert canvas.zoom == canvas.MIN_ZOOM
