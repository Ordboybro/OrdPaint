import json
from pathlib import Path

import pytest
from PySide6.QtGui import QColor, QPainter

from ordpaint.core.document import Document
from ordpaint.core.project import ProjectError, load_project, save_project


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


def test_project_roundtrip_preserves_qpainter_blend_mode(tmp_path: Path, qt_app):
    document = Document(8, 8)
    document.set_layer_blend_mode(
        document.active_index,
        QPainter.CompositionMode.CompositionMode_Multiply,
    )

    path = tmp_path / "blend.ordpaint"
    save_project(document, path)
    restored = load_project(path)

    assert restored.active_layer.blend_mode == QPainter.CompositionMode.CompositionMode_Multiply


def test_load_project_rejects_malformed_json(tmp_path: Path, qt_app):
    path = tmp_path / "broken.ordpaint"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(ProjectError):
        load_project(path)


def test_load_project_rejects_unsupported_version(tmp_path: Path, qt_app):
    path = tmp_path / "future.ordpaint"
    path.write_text(
        json.dumps({"format": "ordpaint", "version": 999, "width": 8, "height": 8, "layers": []}),
        encoding="utf-8",
    )

    with pytest.raises(ProjectError):
        load_project(path)
