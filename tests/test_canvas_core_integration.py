from PySide6.QtCore import QPoint, QRect
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


def test_canvas_clipboard_copy_starts_floating_transform(qt_app):
    clipboard = QGuiApplication.clipboard()
    clipboard.clear()
    document = Document(12, 12)
    document.active_layer.pixmap.fill(QColor("blue"))
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(2, 2, 3, 3))

    assert canvas.copy_selection() is True
    assert clipboard.mimeData().hasImage()
    assert canvas.paste_from_clipboard() is True
    assert canvas.transform_active
    assert len(document.layers) == 1
    assert canvas.selection.active
    assert canvas.selection.rect.topLeft() == QPoint(2, 2)

    assert canvas.commit_transform() is True
    assert not canvas.transform_active
    assert len(document.layers) == 2
    assert document.active_layer.pixmap.toImage().pixelColor(2, 2).blue() == 255


def test_canvas_paste_without_selection_centers_image(qt_app):
    clipboard = QGuiApplication.clipboard()
    clipboard.clear()
    source = Document(4, 4)
    source.active_layer.pixmap.fill(QColor("red"))
    source_canvas = Canvas(source)
    source_canvas.selection.select_all(4, 4)
    assert source_canvas.copy_selection()

    document = Document(20, 20)
    canvas = Canvas(document)
    assert canvas.paste_from_clipboard()
    assert canvas.transform_active
    assert len(document.layers) == 1
    assert canvas.selection.rect.topLeft() == QPoint(8, 8)
    assert canvas.selection.rect.size().width() == 4
    assert canvas.commit_transform()
    assert len(document.layers) == 2


def test_canvas_transform_cancel_keeps_document_unchanged(qt_app):
    document = Document(10, 10)
    document.active_layer.pixmap.fill(QColor("red"))
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(2, 2, 4, 4))
    revision = document.revision

    assert canvas.begin_transform()
    assert canvas.transform_active
    canvas.transform.state.move(QPoint(3, 0))
    assert canvas.cancel_transform()
    assert not canvas.transform_active
    assert document.revision == revision
    assert document.active_layer.pixmap.toImage().pixelColor(2, 2).red() == 255


def test_canvas_transform_commit_moves_pixels_once(qt_app):
    document = Document(10, 10)
    document.active_layer.pixmap.fill(QColor("red"))
    canvas = Canvas(document)
    canvas.selection.set_rect(QRect(1, 1, 3, 3))
    revision = document.revision

    assert canvas.begin_transform()
    canvas.transform.state.move(QPoint(4, 0))
    assert canvas.commit_transform()

    image = document.active_layer.pixmap.toImage()
    assert document.revision == revision + 1
    assert image.pixelColor(1, 1).alpha() == 0
    assert image.pixelColor(5, 1).red() == 255


def test_canvas_zoom_limits(qt_app):
    canvas = Canvas(Document(100, 100))
    canvas.set_zoom(100)
    assert canvas.zoom == canvas.MAX_ZOOM
    canvas.set_zoom(0)
    assert canvas.zoom == canvas.MIN_ZOOM


def test_canvas_grid_and_ruler_settings(qt_app):
    canvas = Canvas(Document(100, 100))
    assert canvas.show_grid is False
    assert canvas.show_rulers is True
    canvas.set_show_grid(True)
    canvas.set_show_rulers(False)
    canvas.set_grid_size(1)
    assert canvas.show_grid is True
    assert canvas.show_rulers is False
    assert canvas.grid_size == 2
