from PySide6.QtCore import QPoint, QPointF, QRect
from PySide6.QtGui import QColor, QImage, QPixmap

from ordpaint.core.document import Document
from ordpaint.core.transform_controller import TransformController


def test_begin_from_selection_does_not_mutate_document():
    document = Document(width=20, height=20)
    document.active_layer.pixmap.fill(QColor("#ff0000"))
    revision = document.revision
    controller = TransformController()

    assert controller.begin_from_selection(document, QRect(2, 3, 5, 4))
    assert controller.active
    assert document.active_layer.pixmap.toImage().pixelColor(2, 3) == QColor("#ff0000")
    assert document.revision == revision


def test_commit_moves_selected_pixels_and_clears_source():
    document = Document(width=20, height=20)
    image = QImage(20, 20, QImage.Format.Format_ARGB32)
    image.fill(QColor("#00000000"))
    image.setPixelColor(1, 1, QColor("#ff0000"))
    document.active_layer.pixmap = QPixmap.fromImage(image)

    controller = TransformController()
    assert controller.begin_from_selection(document, QRect(1, 1, 1, 1))
    controller.state.move(QPointF(5, 0))

    assert controller.commit(document)
    result = document.active_layer.pixmap.toImage()
    assert result.pixelColor(1, 1).alpha() == 0
    assert result.pixelColor(6, 1) == QColor("#ff0000")
    assert not controller.active


def test_begin_paste_creates_layer_only_on_commit():
    document = Document(width=20, height=20)
    controller = TransformController()
    pasted = QImage(3, 2, QImage.Format.Format_ARGB32)
    pasted.fill(QColor("#0000ff"))

    assert controller.begin_paste(pasted, QPointF(4, 5))
    assert len(document.layers) == 1
    assert controller.commit(document)
    assert len(document.layers) == 2
    assert document.active_layer.pixmap.toImage().pixelColor(4, 5) == QColor("#0000ff")


def test_clear_cancels_transform_without_document_change():
    document = Document(width=20, height=20)
    controller = TransformController()
    assert controller.begin_from_selection(document, QRect(0, 0, 5, 5))

    controller.clear()

    assert not controller.active
    assert document.active_layer.pixmap.toImage().pixelColor(QPoint(0, 0)).alpha() == 0
