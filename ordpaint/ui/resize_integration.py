from __future__ import annotations

from types import MethodType

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from ordpaint.ui.resize_dialog import ResizeDialog


def install(window) -> None:
    def resize_canvas(self) -> None:
        dialog = ResizeDialog(self, self.document.width, self.document.height, "Размер холста")
        if dialog.exec() != ResizeDialog.DialogCode.Accepted:
            return
        options = dialog.options()
        if (options.width, options.height) == (self.document.width, self.document.height):
            return
        self._push_history()
        try:
            changed = self.document.resize_canvas(options.width, options.height, options.anchor)
        except ValueError as exc:
            self.history.undo(self.document)
            QMessageBox.warning(self, "Размер холста", str(exc))
            return
        if changed:
            self.dirty = True
            self._refresh_layers()
            self.canvas.update()
            self._update_window_title()

    def scale_image(self) -> None:
        dialog = ResizeDialog(self, self.document.width, self.document.height, "Размер изображения")
        if dialog.exec() != ResizeDialog.DialogCode.Accepted:
            return
        options = dialog.options()
        if (options.width, options.height) == (self.document.width, self.document.height):
            return
        mode = Qt.TransformationMode.SmoothTransformation
        if options.resampling == "fast":
            mode = Qt.TransformationMode.FastTransformation
        self._push_history()
        try:
            changed = self.document.scale_image(options.width, options.height, mode)
        except ValueError as exc:
            self.history.undo(self.document)
            QMessageBox.warning(self, "Размер изображения", str(exc))
            return
        if changed:
            self.dirty = True
            self._refresh_layers()
            self.canvas.update()
            self._update_window_title()

    window.resize_canvas = MethodType(resize_canvas, window)
    window.scale_image = MethodType(scale_image, window)
    for action, callback in (
        (window.resize_canvas_action, window.resize_canvas),
        (window.scale_image_action, window.scale_image),
    ):
        action.triggered.disconnect()
        action.triggered.connect(callback)
