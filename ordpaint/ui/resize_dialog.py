from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox, QVBoxLayout


MAX_PIXELS = 100_000_000


@dataclass(frozen=True)
class ResizeOptions:
    width: int
    height: int
    keep_aspect: bool = False
    anchor: str = "center"
    resampling: str = "smooth"


class ResizeDialog(QDialog):
    """Validated canvas/image resize dialog with preview-oriented controls."""

    def __init__(self, parent=None, width: int = 1280, height: int = 720, title: str = "Изменить размер") -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(380)
        self._initial_ratio = width / height if height else 1.0

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

        self.keep_aspect = QCheckBox("Сохранять пропорции")
        form.addRow("", self.keep_aspect)

        self.anchor_combo = QComboBox()
        anchors = (
            ("Верх-слева", "top-left"),
            ("Сверху", "top"),
            ("Верх-справа", "top-right"),
            ("Слева", "left"),
            ("По центру", "center"),
            ("Справа", "right"),
            ("Снизу-слева", "bottom-left"),
            ("Снизу", "bottom"),
            ("Снизу-справа", "bottom-right"),
        )
        for label, value in anchors:
            self.anchor_combo.addItem(label, value)
        form.addRow("Привязка холста", self.anchor_combo)

        self.resampling_combo = QComboBox()
        self.resampling_combo.addItem("Smooth — качественно", "smooth")
        self.resampling_combo.addItem("Fast — быстро", "fast")
        form.addRow("Ресэмплинг", self.resampling_combo)
        root.addLayout(form)

        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(24)
        root.addWidget(self.preview_label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
        self._buttons = buttons
        self._update_state()
        self.width_spin.valueChanged.connect(self._width_changed)
        self.height_spin.valueChanged.connect(self._height_changed)
        self.keep_aspect.toggled.connect(self._update_state)

    def _width_changed(self, value: int) -> None:
        if self.keep_aspect.isChecked() and self._initial_ratio > 0:
            self.height_spin.blockSignals(True)
            self.height_spin.setValue(max(1, round(value / self._initial_ratio)))
            self.height_spin.blockSignals(False)
        self._update_state()

    def _height_changed(self, value: int) -> None:
        if self.keep_aspect.isChecked() and self._initial_ratio > 0:
            self.width_spin.blockSignals(True)
            self.width_spin.setValue(max(1, round(value * self._initial_ratio)))
            self.width_spin.blockSignals(False)
        self._update_state()

    def _update_state(self) -> None:
        pixels = self.width_spin.value() * self.height_spin.value()
        valid = pixels <= MAX_PIXELS
        self._buttons.button(QDialogButtonBox.StandardButton.Ok).setEnabled(valid)
        self.preview_label.setText(
            f"Результат: {self.width_spin.value()} × {self.height_spin.value()} px · {pixels / 1_000_000:.2f} MP"
        )

    def options(self) -> ResizeOptions:
        return ResizeOptions(
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            keep_aspect=self.keep_aspect.isChecked(),
            anchor=self.anchor_combo.currentData(),
            resampling=self.resampling_combo.currentData(),
        )

    def accept(self) -> None:
        if self.width_spin.value() * self.height_spin.value() > MAX_PIXELS:
            return
        super().accept()
