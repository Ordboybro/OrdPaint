from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QSpinBox, QVBoxLayout


class GridSettingsDialog(QDialog):
    """Small, validated grid configuration dialog."""

    def __init__(self, parent=None, grid_size: int = 16) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки сетки")
        self.setModal(True)
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.size = QSpinBox()
        self.size.setRange(2, 512)
        self.size.setValue(max(2, min(512, int(grid_size))))
        self.major = QSpinBox()
        self.major.setRange(1, 64)
        self.major.setValue(4)
        self.snap = QCheckBox("Привязка к сетке")
        self.snap.setToolTip("Настройка готова для snap-to-grid и не изменяет текущий рисунок.")
        form.addRow("Размер ячейки", self.size)
        form.addRow("Главная линия каждые", self.major)
        layout.addLayout(form)
        layout.addWidget(self.snap)
        layout.addWidget(QLabel("Сетка отображается относительно координат документа и сохраняет размер при изменении масштаба."))
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def grid_size(self) -> int:
        return self.size.value()
