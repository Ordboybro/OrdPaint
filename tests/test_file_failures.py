import json
from pathlib import Path

import pytest

from ordpaint.core.project import ProjectError, load_project


def _write_project(path: Path, image: str = "not-base64") -> None:
    path.write_text(json.dumps({"format": "ordpaint", "version": 1, "width": 4, "height": 4, "active_index": 0, "layers": [{"name": "Layer", "image": image}]}), encoding="utf-8")


def test_corrupted_png_layer_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "broken-image.ordpaint"
    _write_project(path)
    with pytest.raises(ProjectError, match="Повреждены данные изображения"):
        load_project(path)


def test_layer_dimensions_are_validated(tmp_path: Path, qt_app) -> None:
    from PySide6.QtCore import QByteArray, QBuffer, QIODevice
    from PySide6.QtGui import QPixmap

    image = QPixmap(2, 2)
    image.fill()
    data = QByteArray()
    buffer = QBuffer(data)
    assert buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    assert image.save(buffer, "PNG")
    buffer.close()
    path = tmp_path / "wrong-size.ordpaint"
    _write_project(path, bytes(data.toBase64()).decode("ascii"))
    with pytest.raises(ProjectError, match="не совпадает"):
        load_project(path)
