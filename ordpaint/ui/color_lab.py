from __future__ import annotations

import json
import math

from PySide6.QtCore import QPointF, QSettings, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import (
    QDockWidget,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class ColorWheel(QWidget):
    colorSelected = Signal(QColor)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self._image = QImage(180, 180, QImage.Format.Format_ARGB32)
        self._render()

    def _render(self) -> None:
        self._image.fill(Qt.GlobalColor.transparent)
        for y in range(180):
            for x in range(180):
                dx, dy = x - 89.5, y - 89.5
                radius = math.hypot(dx, dy)
                if radius > 88:
                    continue
                hue = (math.degrees(math.atan2(dy, dx)) + 360.0) % 360.0
                saturation = radius / 88.0
                self._image.setPixelColor(x, y, QColor.fromHsvF(hue / 360.0, saturation, 1.0, 1.0))

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.drawImage(0, 0, self._image)
        painter.setPen(QPen(QColor("#ffffff"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(90, 90), 88, 88)
        painter.end()

    def mousePressEvent(self, event) -> None:
        self._pick(event.position())

    def mouseMoveEvent(self, event) -> None:
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._pick(event.position())

    def _pick(self, point: QPointF) -> None:
        x, y = int(point.x()), int(point.y())
        if 0 <= x < 180 and 0 <= y < 180:
            color = self._image.pixelColor(x, y)
            if color.isValid() and color.alpha() > 0:
                self.colorSelected.emit(color)


class ColorLabDock(QDockWidget):
    """HSV/HSL controls, color wheel, foreground/background and persistent palette."""

    SETTINGS_KEY = "ordpaint_palette"

    def __init__(self, window) -> None:
        super().__init__("Color Lab", window)
        self.window = window
        self.settings = QSettings()
        self.foreground = QColor(window.canvas.color)
        self.background = QColor("#ffffff")
        self._syncing = False
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        self.wheel = ColorWheel()
        self.wheel.colorSelected.connect(self._set_color)
        layout.addWidget(self.wheel)
        form = QFormLayout()
        self.h = QSpinBox()
        self.h.setRange(0, 359)
        self.s = QSpinBox()
        self.s.setRange(0, 255)
        self.v = QSpinBox()
        self.v.setRange(0, 255)
        self.hsl_h = QSpinBox()
        self.hsl_h.setRange(0, 359)
        self.hsl_s = QSpinBox()
        self.hsl_s.setRange(0, 255)
        self.hsl_l = QSpinBox()
        self.hsl_l.setRange(0, 255)
        for box in (self.h, self.s, self.v):
            box.valueChanged.connect(self._from_hsv)
        for box in (self.hsl_h, self.hsl_s, self.hsl_l):
            box.valueChanged.connect(self._from_hsl)
        form.addRow("HSV H", self.h)
        form.addRow("HSV S", self.s)
        form.addRow("HSV V", self.v)
        form.addRow("HSL H", self.hsl_h)
        form.addRow("HSL S", self.hsl_s)
        form.addRow("HSL L", self.hsl_l)
        layout.addLayout(form)
        colors = QHBoxLayout()
        self.fg = QPushButton("Передний")
        self.bg = QPushButton("Фон")
        swap = QPushButton("⇄")
        bw = QPushButton("B/W")
        self.fg.clicked.connect(lambda: self._set_color(self.foreground))
        self.bg.clicked.connect(lambda: self._set_color(self.background))
        swap.clicked.connect(self.swap_colors)
        bw.clicked.connect(self.reset_bw)
        for button in (self.fg, self.bg, swap, bw):
            colors.addWidget(button)
        layout.addLayout(colors)
        palette_grid = QGridLayout()
        self.palette_buttons = []
        for index in range(12):
            button = QPushButton()
            button.setFixedSize(28, 28)
            button.clicked.connect(lambda _=False, i=index: self._use_palette(i))
            self.palette_buttons.append(button)
            palette_grid.addWidget(button, index // 6, index % 6)
        layout.addLayout(palette_grid)
        palette_buttons = QHBoxLayout()
        save = QPushButton("Сохранить палитру")
        clear = QPushButton("Очистить палитру")
        save.clicked.connect(self.save_palette)
        clear.clicked.connect(self.clear_palette)
        palette_buttons.addWidget(save)
        palette_buttons.addWidget(clear)
        layout.addLayout(palette_buttons)
        layout.addStretch(1)
        self.setWidget(panel)
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self._palette = self._load_palette()
        self._refresh_palette()
        self._sync(self.foreground)

    def _load_palette(self) -> list[str]:
        try:
            value = json.loads(str(self.settings.value(self.SETTINGS_KEY, "[]")))
            return [str(item) for item in value if QColor(str(item)).isValid()][:12]
        except (TypeError, ValueError, json.JSONDecodeError):
            return []

    def _persist_palette(self) -> None:
        self.settings.setValue(self.SETTINGS_KEY, json.dumps(self._palette))
        self.settings.sync()

    def _set_color(self, color: QColor) -> None:
        color = QColor(color)
        if not color.isValid():
            return
        self.foreground = color
        self.window.canvas.set_color(color)
        self._sync(color)
        self.window.statusBar().showMessage(f"Цвет {color.name(QColor.NameFormat.HexArgb).upper()}", 900)

    def _sync(self, color: QColor) -> None:
        self._syncing = True
        h, s, v, _ = color.getHsv()
        self.h.setValue(max(0, h))
        self.s.setValue(s)
        self.v.setValue(v)
        hh, ss, ll, _ = color.getHsl()
        self.hsl_h.setValue(max(0, hh))
        self.hsl_s.setValue(ss)
        self.hsl_l.setValue(ll)
        self.fg.setStyleSheet(f"background: {self.foreground.name()};")
        self.bg.setStyleSheet(f"background: {self.background.name()};")
        self._syncing = False

    def _from_hsv(self) -> None:
        if not self._syncing:
            self._set_color(QColor.fromHsv(self.h.value(), self.s.value(), self.v.value(), self.foreground.alpha()))

    def _from_hsl(self) -> None:
        if not self._syncing:
            self._set_color(QColor.fromHsl(self.hsl_h.value(), self.hsl_s.value(), self.hsl_l.value(), self.foreground.alpha()))

    def swap_colors(self) -> None:
        self.foreground, self.background = self.background, self.foreground
        self._set_color(self.foreground)

    def reset_bw(self) -> None:
        self.foreground = QColor("#000000")
        self.background = QColor("#ffffff")
        self._set_color(self.foreground)

    def save_palette(self) -> None:
        value = self.foreground.name(QColor.NameFormat.HexArgb)
        if value not in self._palette:
            self._palette.insert(0, value)
        self._palette = self._palette[:12]
        self._persist_palette()
        self._refresh_palette()

    def clear_palette(self) -> None:
        self._palette.clear()
        self._persist_palette()
        self._refresh_palette()

    def _use_palette(self, index: int) -> None:
        if index < len(self._palette):
            self._set_color(QColor(self._palette[index]))

    def _refresh_palette(self) -> None:
        for index, button in enumerate(self.palette_buttons):
            button.setStyleSheet(f"background: {self._palette[index]};" if index < len(self._palette) else "")
