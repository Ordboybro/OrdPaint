from PySide6.QtWidgets import QDialog

from ordpaint.ui.grid_settings_dialog import GridSettingsDialog


def test_grid_settings_defaults(qt_app) -> None:
    dialog = GridSettingsDialog()
    assert dialog.grid_size() == 16
    assert dialog.result() == QDialog.DialogCode.Rejected
    dialog.close()


def test_grid_settings_clamps_initial_value(qt_app) -> None:
    dialog = GridSettingsDialog(grid_size=9999)
    assert dialog.grid_size() == 512
    dialog.close()


def test_grid_settings_changes_value(qt_app) -> None:
    dialog = GridSettingsDialog(grid_size=16)
    dialog.size.setValue(32)
    assert dialog.grid_size() == 32
    dialog.close()
