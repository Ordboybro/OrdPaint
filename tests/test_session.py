from __future__ import annotations

from pathlib import Path

from ordpaint.core.document import Document
from ordpaint.core.session import SessionManager


def test_session_switches_autosave_to_project_and_tracks_recent(tmp_path: Path) -> None:
    project = tmp_path / "demo.ordpaint"
    session = SessionManager(autosave_directory=tmp_path / "recovery")

    session.set_project(project)

    assert session.project_path == project
    assert session.recent.to_list() == [str(project.resolve())]
    assert session.autosave.path.name == ".demo.ordpaint.autosave"


def test_session_autosaves_only_after_revision_changes(tmp_path: Path) -> None:
    session = SessionManager(autosave_directory=tmp_path)
    document = Document(16, 16)

    assert session.tick_autosave(document) is True
    assert session.tick_autosave(document) is False

    document.touch()
    assert session.tick_autosave(document) is True


def test_session_restores_recent_list(tmp_path: Path) -> None:
    first = tmp_path / "first.ordpaint"
    second = tmp_path / "second.ordpaint"
    session = SessionManager(autosave_directory=tmp_path)

    session.restore_recent([str(first), str(second)])

    assert session.serialize_recent() == [str(first.resolve()), str(second.resolve())]


def test_session_recovers_and_discards_document(tmp_path: Path) -> None:
    session = SessionManager(autosave_directory=tmp_path)
    document = Document(24, 12)

    assert session.tick_autosave(document) is True
    assert session.has_recovery() is True

    recovered = session.recover_or_none()

    assert recovered is not None
    assert recovered.width == 24
    assert recovered.height == 12
    assert session.discard_recovery() is True
    assert session.recover_or_none() is None


def test_session_returns_none_for_corrupted_recovery(tmp_path: Path) -> None:
    session = SessionManager(autosave_directory=tmp_path)
    session.recovery_path.parent.mkdir(parents=True, exist_ok=True)
    session.recovery_path.write_bytes(b"broken")

    assert session.has_recovery() is True
    assert session.recover_or_none() is None
