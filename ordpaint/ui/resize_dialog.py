from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QVBoxLayout


MAX_PIXELS = 100_000_000


@dataclass(frozen=True)
class ResizeOptions:
    width: int
    height: int


class ResizeDialog(QDialog):
    """Small validated dialog for canvas/image resizing."""

    def __init__(self, parent=None, width: int = 1280, height: int = 720, title: str = "Изменить размер") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(320)

        root = QVBoxLayout(self)
        form = QFormLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 10000)
        self.width_spin.setValue(max(1, min(10000, width)))
        self.width_spin.setSuffix(" px")
        form.addRow("Ширина", self.width_spin)

        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 10000)
        self.height_spin.setValue(max(1, min(10000, height)))
        self.height_spin.setSuffix(" px")
        form.addRow("Высота", self.height_spin)
        root.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._buttons = buttons
        self._update_buttons()
        self.width_spin.valueChanged.connect(self._update_buttons)
        self.height_spin.valueChanged.connect(self._update_buttons)

    def _update_buttons(self) -> None:
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(
            self.width_spin.value() * self.height_spin.value() <= MAX_PIXELS
        )

    def options(self) -> ResizeOptions:
        return ResizeOptions(self.width_spin.value(), self.height_spin.value())

    def accept(self) -> None:
        if self.width_spin.value() * self.height_spin.value() > MAX_PIXELS:
            return
        super().accept()
