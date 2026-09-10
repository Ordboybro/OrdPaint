from pathlib import Path

from ordpaint.core.autosave import AutosaveManager
from ordpaint.core.document import Document


def test_autosave_rotates_versions_and_recovers(tmp_path: Path) -> None:
    manager = AutosaveManager.for_directory(tmp_path, "test")
    document = Document(8, 8)

    document.touch()
    assert manager.autosave(document)
    first = manager.path.read_bytes()

    document.touch()
    assert manager.autosave(document)
    assert manager.path.exists()
    assert manager._version_path(1).read_bytes() == first
    assert manager.recover().width == 8


def test_corrupt_latest_recovery_can_fall_back_to_previous_version(tmp_path: Path) -> None:
    manager = AutosaveManager.for_directory(tmp_path, "test")
    document = Document(4, 4)
    document.touch()
    assert manager.autosave(document)
    document.touch()
    assert manager.autosave(document)

    manager.path.write_text("not a project", encoding="utf-8")
    recovered = manager.recover(manager._version_path(1))
    assert recovered.width == 4


def test_discard_removes_all_versions(tmp_path: Path) -> None:
    manager = AutosaveManager.for_directory(tmp_path, "test")
    document = Document(4, 4)
    for _ in range(3):
        document.touch()
        manager.autosave(document)
    assert manager.recovery_versions()
    assert manager.discard()
    assert manager.recovery_versions() == []
