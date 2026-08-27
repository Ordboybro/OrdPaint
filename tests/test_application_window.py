from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QApplication

from ordpaint.core.document import Document
from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.settings_store import SettingsStore


def test_integrated_window_replaces_layer_list(qapp: QApplication) -> None:
    window = MainWindow()
    try:
        assert hasattr(window.layers_list, "reorder_requested")
        assert window.autosave_timer.isActive()
    finally:
        window.autosave_timer.stop()
        window.deleteLater()


def test_transform_actions_follow_canvas_after_document_replace(qapp: QApplication) -> None:
    window = MainWindow()
    try:
        window.canvas.select_all()
        window.begin_transform_action.trigger()
        assert window.canvas.transform_active
        window.cancel_transform_action.trigger()
        assert not window.canvas.transform_active
        window._replace_document(Document())
        window.canvas.select_all()
        window.begin_transform_action.trigger()
        assert window.canvas.transform_active
    finally:
        window.autosave_timer.stop()
        window.deleteLater()


def test_recent_projects_round_trip(qapp: QApplication, tmp_path: Path) -> None:
    window = MainWindow()
    store = SettingsStore()
    original_store = window.settings_store
    window.settings_store = store
    project = tmp_path / "example.ordpaint"
    project.write_bytes(b"placeholder")
    try:
        window.session.set_project(project)
        window._save_ui_state()
        assert str(project) in store.load().recent_paths
    finally:
        window.settings_store = original_store
        window.autosave_timer.stop()
        window.deleteLater()
