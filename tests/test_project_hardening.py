from pathlib import Path

import pytest
from PySide6.QtGui import QPixmap

from ordpaint.core.document import Document
from ordpaint.core.project import MAX_PROJECT_BYTES, ProjectError, load_project, save_project


def test_load_rejects_oversized_project(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "large.ordpaint"
    path.write_bytes(b"x" * 32)
    monkeypatch.setattr("ordpaint.core.project.MAX_PROJECT_BYTES", 16)

    with pytest.raises(ProjectError, match="too large"):
        load_project(path)


def test_load_rejects_invalid_utf8(tmp_path: Path) -> None:
    path = tmp_path / "broken.ordpaint"
    path.write_bytes(b"\xff\xfe\xfd")

    with pytest.raises(ProjectError, match="Could not read project"):
        load_project(path)


def test_save_and_load_round_trip(tmp_path: Path, qt_app) -> None:
    document = Document(32, 24)
    pixmap = QPixmap(32, 24)
    pixmap.fill()
    document.active_layer.pixmap = pixmap
    document.touch()
    path = tmp_path / "roundtrip.ordpaint"

    save_project(document, path)
    restored = load_project(path)

    assert restored.width == 32
    assert restored.height == 24
    assert len(restored.layers) == 1
    assert restored.active_index == 0
    assert restored.active_layer.pixmap.size() == pixmap.size()


def test_save_rejects_payload_over_limit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, qt_app) -> None:
    document = Document(16, 16)
    path = tmp_path / "too-large.ordpaint"
    monkeypatch.setattr("ordpaint.core.project.MAX_PROJECT_BYTES", 1)

    with pytest.raises(ProjectError, match="too large"):
        save_project(document, path)


def test_max_project_bytes_is_positive() -> None:
    assert MAX_PROJECT_BYTES > 0
