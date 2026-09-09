from __future__ import annotations

from types import MethodType

from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QVBoxLayout


class TransformDialog(QDialog):
    """Numeric position/size editor for the active transform preview."""

    def __init__(self, parent, state) -> None:
        super().__init__(parent)
        self.setWindowTitle("Трансформация")
        self.setModal(True)
        self.setMinimumWidth(340)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.x_spin = self._spin(state.rect.x(), " px")
        self.y_spin = self._spin(state.rect.y(), " px")
        self.w_spin = self._spin(state.rect.width(), " px")
        self.h_spin = self._spin(state.rect.height(), " px")
        self.keep_aspect = False
        form.addRow("X", self.x_spin)
        form.addRow("Y", self.y_spin)
        form.addRow("Ширина", self.w_spin)
        form.addRow("Высота", self.h_spin)
        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    @staticmethod
    def _spin(value: float, suffix: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(-1000000.0, 1000000.0)
        spin.setDecimals(2)
        spin.setSingleStep(1.0)
        spin.setValue(value)
        spin.setSuffix(suffix)
        return spin


def install(window) -> None:
    menu = next((action.menu() for action in window.menuBar().actions() if action.text() == "Трансформация"), None)
    if menu is None:
        return

    def edit_transform(self) -> None:
        state = self.canvas.transform.state
        if state is None or not state.active:
            return
        dialog = TransformDialog(self, state)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        width = max(1.0, dialog.w_spin.value())
        height = max(1.0, dialog.h_spin.value())
        if width * height > 100_000_000:
            return
        state.rect = state.rect.__class__(
            QPointF(dialog.x_spin.value(), dialog.y_spin.value()),
            QPointF(dialog.x_spin.value() + width, dialog.y_spin.value() + height),
        ).normalized()
        target = state.rect.toAlignedRect().size()
        if target.width() > 0 and target.height() > 0:
            state.image = state.image.scaled(
                target,
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        self.canvas.update()

    window.edit_transform = MethodType(edit_transform, window)
    action = menu.addAction("Числовая трансформация…")
    action.setShortcut("Ctrl+Alt+T")
    action.triggered.connect(window.edit_transform)
    window.numeric_transform_action = action
