from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter

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


def test_exact_layer_reorder_keeps_active_layer(qt_app):
    document = Document(64, 64)
    document.rename_active_layer("Bottom")
    document.add_layer("Middle")
    document.add_layer("Top")
    before = document.revision

    assert document.move_layer(2, 0) is True
    assert [layer.name for layer in document.layers] == ["Top", "Bottom", "Middle"]
    assert document.active_index == 0
    assert document.revision == before + 1
    assert document.move_layer(0, 0) is False
    assert document.move_layer(-1, 0) is False
    assert document.move_layer(0, 3) is False


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


def test_layer_rename_is_unique_and_touches_document(qt_app):
    document = Document(32, 32)
    document.add_layer("Layer")
    before = document.revision
    assert document.rename_layer(1, "Layer 1") is True
    assert document.layers[1].name == "Layer 1 2"
    assert document.revision == before + 1
    assert document.rename_layer(1, "Layer 1 2") is False


def test_blend_mode_change_touches_document(qt_app):
    document = Document(32, 32)
    before = document.revision
    mode = QPainter.CompositionMode.CompositionMode_Multiply
    assert document.set_layer_blend_mode(0, mode) is True
    assert document.active_layer.blend_mode == mode
    assert document.revision == before + 1
    assert document.set_layer_blend_mode(0, mode) is False


def test_clear_locked_layer_is_rejected(qt_app):
    document = Document(16, 16)
    document.active_layer.pixmap.fill(Qt.GlobalColor.black)
    document.set_layer_locked(0, True)
    assert document.clear_active_layer() is False
    assert document.active_layer.pixmap.toImage().pixelColor(0, 0).alpha() != 0


def test_merge_visible_combines_visible_layers(qt_app):
    document = Document(16, 16)
    document.active_layer.pixmap.fill(Qt.GlobalColor.red)
    document.add_layer("Top")
    document.active_layer.pixmap.fill(Qt.GlobalColor.blue)
    document.add_layer("Hidden")
    document.set_layer_visibility(document.active_index, False)

    assert document.merge_visible() is True
    assert len(document.layers) == 2
    assert document.layers[0].pixmap.toImage().pixelColor(0, 0).blue() > 0
    assert document.layers[1].name == "Hidden"


def test_merge_rejects_locked_destination(qt_app):
    document = Document(16, 16)
    document.set_layer_locked(0, True)
    document.add_layer("Top")
    assert document.merge_active_down() is False
    document.set_active_index(0)
    assert document.merge_visible() is False


def test_resize_canvas_preserves_pixels_and_layers(qt_app):
    document = Document(4, 4)
    document.active_layer.pixmap.fill(Qt.GlobalColor.transparent)
    document.active_layer.pixmap.setMask(document.active_layer.pixmap.createMaskFromColor(Qt.GlobalColor.transparent))
    painter = QPainter(document.active_layer.pixmap)
    painter.fillRect(1, 1, 2, 2, Qt.GlobalColor.red)
    painter.end()
    document.add_layer("Top")
    document.active_layer.pixmap.fill(Qt.GlobalColor.blue)

    assert document.resize_canvas(8, 8, "center") is True
    assert (document.width, document.height) == (8, 8)
    assert len(document.layers) == 2
    assert document.layers[0].pixmap.toImage().pixelColor(3, 3).red() > 0
    assert document.layers[1].pixmap.toImage().pixelColor(0, 0).blue() == 0
    assert document.layers[1].pixmap.toImage().pixelColor(2, 2).blue() > 0


def test_resize_canvas_rejects_invalid_anchor_and_dimensions(qt_app):
    document = Document(8, 8)
    try:
        document.resize_canvas(16, 16, "bad-anchor")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid anchor must raise ValueError")
    assert document.resize_canvas(0, 16) is False
    assert document.resize_canvas(8, 8) is False


def test_scale_image_resizes_all_layers(qt_app):
    document = Document(4, 3)
    document.add_layer("Top")
    before_revision = document.revision
    assert document.scale_image(8, 6) is True
    assert (document.width, document.height) == (8, 6)
    assert all(layer.pixmap.size().width() == 8 and layer.pixmap.size().height() == 6 for layer in document.layers)
    assert document.revision == before_revision + 1
