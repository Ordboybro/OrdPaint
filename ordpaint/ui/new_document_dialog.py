from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout, QHBoxLayout, QLabel, QSpinBox, QVBoxLayout


@dataclass(frozen=True)
class NewDocumentOptions:
    width: int
    height: int
    transparent: bool
    background: str
    anchor: str = "center"


class NewDocumentDialog(QDialog):
    """Validated document-creation dialog shared by the editor UI."""

    def __init__(self, parent=None, width: int = 1280, height: int = 720) -> None:
        super().__init__(parent)
        self.setWindowTitle("Новый документ")
        self.setModal(True)
        self.setMinimumWidth(360)

        root = QVBoxLayout(self)
        heading = QLabel("Создать новый документ")
        heading.setStyleSheet("font-size: 17px; font-weight: 700;")
        root.addWidget(heading)
        subtitle = QLabel("Задайте размер холста и параметры фона.")
        subtitle.setStyleSheet("color: #8f96a3;")
        root.addWidget(subtitle)

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

        self.preset_combo = QComboBox()
        self.preset_combo.addItem("1280 × 720", (1280, 720))
        self.preset_combo.addItem("1920 × 1080", (1920, 1080))
        self.preset_combo.addItem("2048 × 2048", (2048, 2048))
        self.preset_combo.addItem("4096 × 4096", (4096, 4096))
        self.preset_combo.addItem("Пользовательский", None)
        self.preset_combo.currentIndexChanged.connect(self._apply_preset)
        form.addRow("Пресет", self.preset_combo)

        self.transparent_check = QCheckBox("Прозрачный фон")
        self.transparent_check.setChecked(True)
        self.transparent_check.toggled.connect(self._toggle_background)
        form.addRow("Фон", self.transparent_check)

        self.background_combo = QComboBox()
        self.background_combo.addItem("Белый", "white")
        self.background_combo.addItem("Чёрный", "black")
        self.background_combo.addItem("Серый", "#808080")
        self.background_combo.setEnabled(False)
        form.addRow("Цвет", self.background_combo)

        self.anchor_combo = QComboBox()
        for label, value in (
            ("По центру", "center"),
            ("Слева сверху", "top-left"),
            ("Сверху", "top"),
            ("Справа сверху", "top-right"),
            ("Слева", "left"),
            ("Справа", "right"),
            ("Слева снизу", "bottom-left"),
            ("Снизу", "bottom"),
            ("Справа снизу", "bottom-right"),
        ):
            self.anchor_combo.addItem(label, value)
        form.addRow("Якорь", self.anchor_combo)
        root.addLayout(form)

        size_hint = QLabel()
        size_hint.setStyleSheet("color: #8f96a3;")
        root.addWidget(size_hint)
        self._size_hint = size_hint
        self._update_size_hint()
        self.width_spin.valueChanged.connect(self._update_size_hint)
        self.height_spin.valueChanged.connect(self._update_size_hint)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)

    def _apply_preset(self, index: int) -> None:
        value = self.preset_combo.itemData(index)
        if value is None:
            return
        width, height = value
        self.width_spin.setValue(width)
        self.height_spin.setValue(height)

    def _toggle_background(self, transparent: bool) -> None:
        self.background_combo.setEnabled(not transparent)

    def _update_size_hint(self) -> None:
        pixels = self.width_spin.value() * self.height_spin.value()
        megapixels = pixels / 1_000_000
        self._size_hint.setText(f"{self.width_spin.value()} × {self.height_spin.value()} px  •  {megapixels:.2f} MP")

    def options(self) -> NewDocumentOptions:
        return NewDocumentOptions(
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            transparent=self.transparent_check.isChecked(),
            background=str(self.background_combo.currentData()),
            anchor=str(self.anchor_combo.currentData()),
        )

    def accept(self) -> None:
        if self.width_spin.value() * self.height_spin.value() > 100_000_000:
            self._size_hint.setText("Слишком большой документ: максимум 100 MP.")
            return
        super().accept()
