from PySide6.QtCore import Qt

from ordpaint.core.document import Document
from ordpaint.core.project import load_project, save_project


def test_project_roundtrip_preserves_layers_and_properties(qt_app, tmp_path):
    document = Document(24, 16)
    document.active_layer.pixmap.fill(Qt.GlobalColor.red)
    document.active_layer.name = "Background"
    document.active_layer.opacity = 72
    document.active_layer.locked = True

    document.add_layer("Details")
    document.active_layer.pixmap.fill(Qt.GlobalColor.blue)
    document.active_layer.visible = False
    document.active_index = 0

    path = tmp_path / "roundtrip.ordpaint"
    save_project(document, path)
    loaded = load_project(path)

    assert loaded.width == 24
    assert loaded.height == 16
    assert loaded.active_index == 0
    assert [layer.name for layer in loaded.layers] == ["Background", "Details"]
    assert loaded.layers[0].opacity == 72
    assert loaded.layers[0].locked is True
    assert loaded.layers[1].visible is False
    assert loaded.layers[0].pixmap.toImage().pixelColor(0, 0).red() == 255
