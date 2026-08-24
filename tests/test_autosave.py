from ordpaint.core.autosave import AutosaveManager
from ordpaint.core.document import Document


def test_autosave_writes_once_per_revision(tmp_path):
    document = Document(width=12, height=8)
    manager = AutosaveManager.for_directory(tmp_path, "demo")

    assert manager.autosave(document)
    assert manager.path.exists()
    assert not manager.autosave(document)

    document.touch()
    assert manager.autosave(document)


def test_autosave_recovers_document(tmp_path):
    document = Document(width=12, height=8)
    document.active_layer.name = "Background"
    manager = AutosaveManager.for_directory(tmp_path, "demo")

    assert manager.autosave(document)
    recovered = manager.recover()

    assert recovered.width == 12
    assert recovered.height == 8
    assert recovered.active_layer.name == "Background"


def test_discard_removes_recovery_file(tmp_path):
    manager = AutosaveManager.for_directory(tmp_path, "demo")
    assert manager.autosave(Document(width=5, height=5))

    assert manager.discard()
    assert not manager.has_recovery()
    assert not manager.discard()


def test_autosave_path_is_stable_for_project(tmp_path):
    manager = AutosaveManager.for_project(tmp_path / "painting.ordpaint")

    assert manager.path.name == ".painting.ordpaint.autosave"
