from PySide6.QtWidgets import QDialogButtonBox

from ordpaint.ui.resize_dialog import ResizeDialog


def test_resize_dialog_defaults(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    assert dialog.options().width == 800
    assert dialog.options().height == 600


def test_resize_dialog_disables_oversized_documents(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    dialog.width_spin.setValue(10000)
    dialog.height_spin.setValue(10000)
    assert not dialog._buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()
