from PySide6.QtWidgets import QDialogButtonBox

from ordpaint.ui.resize_dialog import ResizeDialog


def test_resize_dialog_defaults(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    options = dialog.options()
    assert options.width == 800
    assert options.height == 600
    assert options.anchor == "center"
    assert options.resampling == "smooth"


def test_resize_dialog_disables_oversized_documents(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    dialog.width_spin.setValue(10000)
    dialog.height_spin.setValue(10000)
    assert not dialog._buttons.button(QDialogButtonBox.StandardButton.Ok).isEnabled()


def test_resize_dialog_keeps_aspect_ratio(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    dialog.keep_aspect.setChecked(True)
    dialog.width_spin.setValue(400)
    assert dialog.height_spin.value() == 300


def test_resize_dialog_returns_anchor_and_fast_resampling(qt_app):
    dialog = ResizeDialog(width=800, height=600)
    dialog.anchor_combo.setCurrentIndex(8)
    dialog.resampling_combo.setCurrentIndex(1)
    options = dialog.options()
    assert options.anchor == "bottom-right"
    assert options.resampling == "fast"
