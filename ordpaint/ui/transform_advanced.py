from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QTransform
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QVBoxLayout


class AngleDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Произвольный угол")
        form = QFormLayout()
        self.angle = QDoubleSpinBox()
        self.angle.setRange(-3600.0, 3600.0)
        self.angle.setDecimals(2)
        self.angle.setSingleStep(1.0)
        self.angle.setSuffix("°")
        form.addRow("Угол", self.angle)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)


def install(window) -> None:
    menu = next((action.menu() for action in window.menuBar().actions() if action.text() == "Трансформация"), None)
    if menu is None:
        return

    def rotate_any() -> None:
        state = window.canvas.transform.state
        if state is None or not state.active:
            return
        dialog = AngleDialog(window)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        centre = state.rect.center()
        image = state.image.transformed(QTransform().rotate(dialog.angle.value()), Qt.TransformationMode.SmoothTransformation)
        state.image = image
        state.rect = QRectF(centre.x() - image.width() / 2, centre.y() - image.height() / 2, image.width(), image.height())
        window.canvas.update()

    action = menu.addAction("Произвольный угол…")
    action.setShortcut("Ctrl+Alt+R")
    action.triggered.connect(rotate_any)
    window.arbitrary_rotate_action = action
