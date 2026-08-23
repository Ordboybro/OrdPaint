from PySide6.QtCore import Qt
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


def test_layer_properties_are_clamped(qt_app):
    document = Document(32, 32)
    document.set_layer_opacity(0, 150)
    assert document.active_layer.opacity == 100
    document.set_layer_opacity(0, -20)
    assert document.active_layer.opacity == 0
    document.set_layer_visibility(0, False)
    document.set_layer_locked(0, True)
    assert document.active_layer.visible is False
    assert document.active_layer.locked is True


def test_clear_locked_layer_is_rejected(qt_app):
    document = Document(16, 16)
    document.active_layer.pixmap.fill(Qt.GlobalColor.black)
    document.set_layer_locked(0, True)
    assert document.clear_active_layer() is False
    assert not document.active_layer.pixmap.toImage().pixelColor(0, 0).alpha() == 0


def test_merge_visible_combines_visible_layers(qt_app):
    document = Document(16, 16)
    document.active_layer.pixmap.fill(Qt.GlobalColor.red)
    document.add_layer("Top")
    document.active_layer.pixmap.fill(Qt.GlobalColor.blue)
    document.add_layer("Hidden")
    document.active_layer.visible = False

    assert document.merge_visible() is True
    assert len(document.layers) == 2
    assert document.layers[0].pixmap.toImage().pixelColor(0, 0).blue() > 0
    assert document.layers[1].name == "Hidden"
