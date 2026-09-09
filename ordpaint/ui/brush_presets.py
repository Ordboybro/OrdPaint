from __future__ import annotations

import json

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QComboBox, QDockWidget, QHBoxLayout, QLabel, QPushButton, QInputDialog, QVBoxLayout, QWidget


DEFAULT_PRESETS = {
    "Basic": {"size": 8, "opacity": 100, "hardness": 100, "spacing": 20, "smoothness": 0},
    "Soft": {"size": 24, "opacity": 55, "hardness": 25, "spacing": 18, "smoothness": 15},
    "Hard": {"size": 8, "opacity": 100, "hardness": 100, "spacing": 12, "smoothness": 0},
    "Pencil": {"size": 3, "opacity": 90, "hardness": 100, "spacing": 8, "smoothness": 10},
    "Ink": {"size": 5, "opacity": 100, "hardness": 95, "spacing": 10, "smoothness": 25},
    "Marker": {"size": 18, "opacity": 65, "hardness": 65, "spacing": 16, "smoothness": 30},
    "Eraser": {"size": 20, "opacity": 100, "hardness": 80, "spacing": 18, "smoothness": 10},
}


class BrushPresetDock(QDockWidget):
    """Persistent, editable brush preset collection."""

    SETTINGS_KEY = "brush_presets"

    def __init__(self, window) -> None:
        super().__init__("Пресеты кисти", window)
        self.window = window
        self.settings = QSettings()
        self.presets = self._load()
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        row = QHBoxLayout()
        row.addWidget(QLabel("Пресет"))
        self.combo = QComboBox()
        self.combo.addItems(self.presets)
        self.combo.currentTextChanged.connect(self.apply_selected)
        row.addWidget(self.combo, 1)
        layout.addLayout(row)
        buttons = QHBoxLayout()
        for text, callback in (("Сохранить", self.save_current), ("Удалить", self.delete_selected)):
            button = QPushButton(text)
            button.clicked.connect(callback)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        hint = QLabel("Двойной шаг: выберите пресет, затем меняйте параметры кисти. Сохранение запоминает текущие настройки.")
        hint.setWordWrap(True)
        hint.setProperty("secondary", True)
        layout.addWidget(hint)
        layout.addStretch(1)
        self.setWidget(panel)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)

    def _load(self) -> dict[str, dict[str, int]]:
        raw = self.settings.value(self.SETTINGS_KEY, "")
        if not raw:
            return {name: dict(values) for name, values in DEFAULT_PRESETS.items()}
        try:
            data = json.loads(str(raw))
            if not isinstance(data, dict):
                raise ValueError
            result = {name: {key: int(value) for key, value in values.items()} for name, values in data.items() if isinstance(name, str) and isinstance(values, dict)}
            return result or {name: dict(values) for name, values in DEFAULT_PRESETS.items()}
        except (TypeError, ValueError, json.JSONDecodeError):
            return {name: dict(values) for name, values in DEFAULT_PRESETS.items()}

    def _persist(self) -> None:
        self.settings.setValue(self.SETTINGS_KEY, json.dumps(self.presets, ensure_ascii=False))
        self.settings.sync()

    def apply_selected(self, name: str) -> None:
        values = self.presets.get(name)
        if not values:
            return
        canvas = self.window.canvas
        canvas.set_brush_size(values.get("size", 8))
        canvas.set_opacity(values.get("opacity", 100))
        if hasattr(canvas, "set_brush_hardness"):
            canvas.set_brush_hardness(values.get("hardness", 100))
        if hasattr(canvas, "set_brush_spacing"):
            canvas.set_brush_spacing(values.get("spacing", 20))
        if hasattr(canvas, "set_brush_smoothness"):
            canvas.set_brush_smoothness(values.get("smoothness", 0))
        self.window.statusBar().showMessage(f"Пресет кисти: {name}", 1200)

    def save_current(self) -> None:
        name, ok = QInputDialog.getText(self, "Сохранить пресет", "Название:", text=self.combo.currentText())
        if not ok or not name.strip():
            return
        canvas = self.window.canvas
        self.presets[name.strip()] = {
            "size": int(canvas.brush_size),
            "opacity": int(canvas.opacity),
            "hardness": int(getattr(canvas, "brush_hardness", 100)),
            "spacing": int(getattr(canvas, "brush_spacing", 20)),
            "smoothness": int(getattr(canvas, "brush_smoothness", 0)),
        }
        self._persist()
        self.combo.blockSignals(True)
        self.combo.clear()
        self.combo.addItems(self.presets)
        self.combo.setCurrentText(name.strip())
        self.combo.blockSignals(False)

    def delete_selected(self) -> None:
        name = self.combo.currentText()
        if not name or name not in self.presets:
            return
        if name in DEFAULT_PRESETS:
            self.window.statusBar().showMessage("Встроенный пресет нельзя удалить", 1600)
            return
        self.presets.pop(name, None)
        self._persist()
        self.combo.removeItem(self.combo.findText(name))
