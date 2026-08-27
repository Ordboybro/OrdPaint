from PySide6.QtCore import Qt

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
    assert document.set_layer_blend_mode(0, Qt.CompositionMode.CompositionMode_Multiply) is True
    assert document.active_layer.blend_mode == Qt.CompositionMode.CompositionMode_Multiply
    assert document.revision == before + 1
    assert document.set_layer_blend_mode(0, Qt.CompositionMode.CompositionMode_Multiply) is False


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
