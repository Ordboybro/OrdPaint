from PySide6.QtGui import QGuiApplication

from ordpaint.core.document import Document


def test_document_has_one_layer(qt_app):
    document = Document(64, 64)
    assert len(document.layers) == 1
    assert document.active_layer.pixmap.size().width() == 64


def test_layer_move_and_duplicate(qt_app):
    document = Document(64, 64)
    document.add_layer("Top")
    assert document.active_layer.name == "Top"
    document.move_active_layer(-1)
    assert document.active_index == 0
    duplicate = document.duplicate_active_layer()
    assert duplicate.name.startswith("Top copy")


def test_remove_keeps_one_layer(qt_app):
    document = Document(32, 32)
    assert document.remove_active_layer() is False
