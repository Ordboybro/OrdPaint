from pathlib import Path

from PySide6.QtGui import QColor, QPainter

from ordpaint.core.document import Document
from ordpaint.core.project import load_project, save_project


def test_project_roundtrip(tmp_path: Path, qt_app):
    document = Document(24, 16)
    document.add_layer("Paint")
    painter = QPainter(document.active_layer.pixmap)
    painter.fillRect(0, 0, 10, 10, QColor("red"))
    painter.end()

    path = tmp_path / "sample.ordpaint"
    save_project(document, path)
    restored = load_project(path)

    assert restored.width == 24
    assert restored.height == 16
    assert len(restored.layers) == 2
    assert restored.active_layer.name == "Paint"
    assert restored.active_layer.pixmap.toImage().pixelColor(1, 1) == QColor("red")
