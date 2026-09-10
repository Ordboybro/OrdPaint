from __future__ import annotations

from types import MethodType

from PySide6.QtWidgets import QMessageBox


def install(window) -> None:
    """Replace the binary recovery prompt with explicit Restore/Delete/Later choices."""
    def offer_recovery(self) -> None:
        recovered = self.session.recover_or_none()
        if recovered is None:
            return
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Восстановление проекта")
        box.setText("Найден черновик после предыдущего завершения OrdPaint.")
        box.setInformativeText("Выберите, что сделать с восстановленной версией.")
        restore = box.addButton("Восстановить", QMessageBox.ButtonRole.AcceptRole)
        later = box.addButton("Позже", QMessageBox.ButtonRole.DestructiveRole)
        discard = box.addButton("Удалить", QMessageBox.ButtonRole.RejectRole)
        box.exec()
        clicked = box.clickedButton()
        if clicked is restore:
            self.history.clear()
            self.current_path = None
            self.session.set_project(None)
            self.dirty = True
            self._replace_document(recovered)
            self._update_window_title()
        elif clicked is discard:
            self.session.discard_recovery()
        # "Позже" deliberately leaves the recovery snapshot untouched for the next launch.

    window._offer_recovery = MethodType(offer_recovery, window)
