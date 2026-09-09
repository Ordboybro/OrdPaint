from PySide6.QtWidgets import QDialog

from ordpaint.ui.new_document_dialog import NewDocumentDialog


def test_new_document_dialog_defaults(qapp):
    dialog = NewDocumentDialog(width=1920, height=1080)
    try:
        assert dialog.width_spin.value() == 1920
        assert dialog.height_spin.value() == 1080
        assert dialog.transparent_check.isChecked()
        assert dialog.background_combo.isEnabled() is False
        assert dialog.options().anchor == "center"
    finally:
        dialog.close()
        dialog.deleteLater()


def test_new_document_dialog_preset_updates_dimensions(qapp):
    dialog = NewDocumentDialog()
    try:
        dialog.preset_combo.setCurrentIndex(1)
        assert dialog.width_spin.value() == 1920
        assert dialog.height_spin.value() == 1080
        dialog.preset_combo.setCurrentIndex(4)
        dialog.width_spin.setValue(800)
        dialog.height_spin.setValue(600)
        assert dialog.options().width == 800
        assert dialog.options().height == 600
    finally:
        dialog.close()
        dialog.deleteLater()


def test_new_document_dialog_background_toggle(qapp):
    dialog = NewDocumentDialog()
    try:
        dialog.transparent_check.setChecked(False)
        assert dialog.background_combo.isEnabled()
        dialog.background_combo.setCurrentIndex(1)
        assert dialog.options().background == "black"
        dialog.transparent_check.setChecked(True)
        assert not dialog.background_combo.isEnabled()
    finally:
        dialog.close()
        dialog.deleteLater()


def test_new_document_dialog_rejects_over_100_mp(qapp):
    dialog = NewDocumentDialog()
    try:
        dialog.width_spin.setValue(10000)
        dialog.height_spin.setValue(10000)
        dialog.accept()
        assert dialog.result() != QDialog.DialogCode.Accepted
    finally:
        dialog.close()
        dialog.deleteLater()
