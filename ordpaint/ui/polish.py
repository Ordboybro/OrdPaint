from __future__ import annotations

from collections import deque

from PySide6.QtCore import QByteArray, QPointF, QRect, Qt
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QColorDialog,
    QDockWidget,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ordpaint.core.raster import flood_fill
from ordpaint.ui.canvas import Canvas


_ICON_PATHS = {
    "brush": "M4 20c3-1 4-4 7-7l7-7 2 2-7 7c-3 3-6 4-7 5l-2 0z",
    "eraser": "M5 16l8-8 5 5-8 8H5l-2-3 2-2z",
    "line": "M4 20L20 4",
    "rectangle": "M4 5h16v14H4z",
    "ellipse": "M4 12a8 6 0 1 0 16 0a8 6 0 1 0-16 0",
    "fill": "M6 4l10 10-4 4L2 8z M15 17h6v3h-6z",
    "eyedropper": "M14 4l6 6-2 2-2-2-7 7H5v-4l7-7-2-2 2-2z",
    "select": "M4 4h7v2H6v5H4zm9 0h7v7h-2V6h-5zM4 13h2v5h5v2H4zm14 0h2v7h-7v-2h5z",
    "undo": "M9 7H4l4-4v3c6 0 10 3 10 8 0 2-1 4-3 5 1-2 1-4 0-6-1-3-3-6-6-6v0z",
    "redo": "M15 7h5l-4-4v3C10 6 6 9 6 14c0 2 1 4 3 5-1-2-1-4 0-6 1-3 3-6 6-6v0z",
}


def _icon(name: str) -> QIcon:
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">'
        f'<path d="{_ICON_PATHS[name]}" fill="none" stroke="#ff7a00" stroke-width="1.8" '
        'stroke-linecap="round" stroke-linejoin="round"/></svg>'
    )
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def _install_canvas_dynamics() -> None:
    if getattr(Canvas, "_ordpaint_dynamics_installed", False):
        return

    def set_hardness(self, value: int) -> None:
        self.brush_hardness = max(1, min(100, int(value)))
        self.update()

    def set_spacing(self, value: int) -> None:
        self.brush_spacing = max(1, min(100, int(value)))
        self.update()

    def set_smoothness(self, value: int) -> None:
        self.brush_smoothness = max(0, min(100, int(value)))
        self.update()

    def set_fill_tolerance(self, value: int) -> None:
        self.fill_tolerance = max(0, min(255, int(value)))
        self.update()

    def draw_segment(self, start, end) -> None:
        layer = self.document.active_layer
        if layer.locked:
            return
        radius = max(0.5, self.brush_size / 2)
        spacing = max(0.01, self.brush_spacing / 100)
        smoothness = max(0, min(100, self.brush_smoothness)) / 100
        step = max(1.0, radius * 2 * spacing * (1.0 - smoothness * 0.45))
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        distance = (dx * dx + dy * dy) ** 0.5
        count = max(1, int(distance / step) + 1)
        painter = QPainter(layer.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        if self.selection.rect is not None:
            painter.setClipRect(self.selection.rect)
        erase = self.tool.value == "eraser"
        if erase:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        for index in range(count + 1):
            t = min(1.0, index / max(1, count))
            point = QPointF(start.x() + dx * t, start.y() + dy * t)
            if self.brush_hardness >= 99:
                color = QColor(self.color)
                color.setAlpha(round(color.alpha() * self.opacity / 100))
                painter.setBrush(QBrush(color))
            else:
                color = QColor(self.color)
                color.setAlpha(round(color.alpha() * self.opacity / 100))
                gradient = QRadialGradient(point, radius)
                hard_stop = self.brush_hardness / 100
                gradient.setColorAt(0.0, color)
                gradient.setColorAt(hard_stop, color)
                edge = QColor(color)
                edge.setAlpha(0)
                gradient.setColorAt(1.0, edge)
                painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(point, radius, radius)
        painter.end()
        self.document.touch()
        self.document_changed.emit()

    def fill(self, point) -> None:
        if flood_fill(
            self.document.active_layer.pixmap,
            point,
            self._paint_color(),
            tolerance=self.fill_tolerance,
            clip=self.selection.rect,
        ):
            self.document.touch()
            self.document_changed.emit()

    original_init = Canvas.__init__

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self.brush_hardness = 100
        self.brush_spacing = 20
        self.brush_smoothness = 0
        self.fill_tolerance = 0

    Canvas.__init__ = init
    Canvas.set_brush_hardness = set_hardness
    Canvas.set_brush_spacing = set_spacing
    Canvas.set_brush_smoothness = set_smoothness
    Canvas.set_fill_tolerance = set_fill_tolerance
    Canvas._draw_segment = draw_segment
    Canvas._flood_fill = fill
    Canvas._ordpaint_dynamics_installed = True


class ColorStudio(QWidget):
    """Compact RGBA/HEX color panel with recent swatches."""

    def __init__(self, window) -> None:
        super().__init__()
        self.window = window
        self._recent: deque[str] = deque(maxlen=12)
        self._syncing = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.preview = QPushButton()
        self.preview.setMinimumHeight(42)
        self.preview.clicked.connect(self._choose)
        layout.addWidget(self.preview)
        form = QFormLayout()
        self.hex_edit = QLineEdit()
        self.hex_edit.setPlaceholderText("#RRGGBB or #AARRGGBB")
        self.hex_edit.returnPressed.connect(self._apply_hex)
        form.addRow("HEX", self.hex_edit)
        self.r = QSpinBox(); self.r.setRange(0, 255)
        self.g = QSpinBox(); self.g.setRange(0, 255)
        self.b = QSpinBox(); self.b.setRange(0, 255)
        self.a = QSpinBox(); self.a.setRange(0, 255)
        for box in (self.r, self.g, self.b, self.a):
            box.valueChanged.connect(self._apply_rgba)
        form.addRow("R", self.r); form.addRow("G", self.g); form.addRow("B", self.b); form.addRow("A", self.a)
        layout.addLayout(form)
        self.swatches = QWidget()
        self.swatch_grid = QGridLayout(self.swatches)
        self.swatch_grid.setContentsMargins(0, 0, 0, 0)
        self.swatch_grid.setSpacing(4)
        layout.addWidget(self.swatches)
        layout.addStretch(1)
        self.sync(window.canvas.color)

    def sync(self, color: QColor) -> None:
        color = QColor(color)
        self._syncing = True
        self.r.setValue(color.red()); self.g.setValue(color.green()); self.b.setValue(color.blue()); self.a.setValue(color.alpha())
        self.hex_edit.setText(color.name(QColor.NameFormat.HexArgb).upper())
        self.preview.setStyleSheet(f"background: rgba({color.red()},{color.green()},{color.blue()},{color.alpha() / 255:.3f});")
        self._syncing = False

    def _choose(self) -> None:
        color = QColorDialog.getColor(self.window.canvas.color, self, "Цвет")
        if color.isValid():
            self._set(color)

    def _apply_hex(self) -> None:
        color = QColor(self.hex_edit.text().strip())
        if color.isValid():
            self._set(color)

    def _apply_rgba(self) -> None:
        if self._syncing:
            return
        self._set(QColor(self.r.value(), self.g.value(), self.b.value(), self.a.value()))

    def _set(self, color: QColor) -> None:
        self.window.canvas.set_color(color)
        self.sync(color)
        value = color.name(QColor.NameFormat.HexArgb).upper()
        if value not in self._recent:
            self._recent.appendleft(value)
        self._rebuild_swatches()

    def _rebuild_swatches(self) -> None:
        while self.swatch_grid.count():
            item = self.swatch_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        for index, value in enumerate(self._recent):
            button = QPushButton()
            button.setFixedSize(28, 28)
            button.setStyleSheet(f"background: {value}; border: 1px solid #555; border-radius: 4px;")
            button.clicked.connect(lambda _=False, v=value: self._set(QColor(v)))
            self.swatch_grid.addWidget(button, index // 4, index % 4)


def _add_brush_controls(window) -> None:
    dock = QDockWidget("Кисть", window)
    dock.setObjectName("brushSettingsDock")
    panel = QWidget()
    layout = QVBoxLayout(panel)
    layout.setContentsMargins(10, 10, 10, 10)
    controls = (
        ("Жёсткость", "brush_hardness", 1, 100, 100),
        ("Интервал", "brush_spacing", 1, 100, 20),
        ("Сглаживание", "brush_smoothness", 0, 100, 0),
        ("Допуск заливки", "fill_tolerance", 0, 255, 0),
    )
    for label, attr, minimum, maximum, value in controls:
        row = QHBoxLayout()
        row.addWidget(QLabel(label))
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(minimum, maximum)
        slider.setValue(getattr(window.canvas, attr, value))
        value_label = QLabel(str(slider.value()))
        row.addWidget(slider, 1)
        row.addWidget(value_label)
        setter = getattr(window.canvas, f"set_{attr}")
        slider.valueChanged.connect(setter)
        slider.valueChanged.connect(value_label.setNum)
        layout.addLayout(row)
    layout.addStretch(1)
    dock.setWidget(panel)
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)


def install(window) -> None:
    _install_canvas_dynamics()
    for attr in ("brush_hardness", "brush_spacing", "brush_smoothness", "fill_tolerance"):
        if not hasattr(window.canvas, attr):
            setattr(window.canvas, attr, {"brush_hardness": 100, "brush_spacing": 20, "brush_smoothness": 0, "fill_tolerance": 0}[attr])
    window.setWindowIcon(_icon("brush"))
    if hasattr(window, "grid_action"):
        window.grid_action.setShortcut("Ctrl+G")
        window.grid_action.setToolTip("Сетка (Ctrl+G)")
    for attr, name in {"new_action": "brush", "open_action": "select", "save_action": "fill", "export_action": "select", "undo_action": "undo", "redo_action": "redo"}.items():
        action = getattr(window, attr, None)
        if action is not None:
            action.setIcon(_icon(name))
    tool_icons = {"Кисть": "brush", "Ластик": "eraser", "Линия": "line", "Прямоугольник": "rectangle", "Эллипс": "ellipse", "Заливка": "fill", "Пипетка": "eyedropper", "Выделение": "select"}
    for button in window.findChildren(QToolButton):
        if button.objectName() != "toolPaletteButton":
            continue
        action = button.defaultAction()
        name = tool_icons.get(action.text() if action is not None else "")
        if name is not None:
            button.setIcon(_icon(name))
            button.setText("")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            button.setToolTip(f"{action.text()}  •  {action.shortcut().toString()}")
    _add_brush_controls(window)
    dock = QDockWidget("Цвет", window)
    dock.setObjectName("colorStudioDock")
    dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
    studio = ColorStudio(window)
    dock.setWidget(studio)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
    window.color_studio = studio
    window.canvas.color_picked.connect(studio.sync)
    view_menu = next((action.menu() for action in window.menuBar().actions() if action.text() == "Вид"), None)
    if view_menu is not None:
        grid_settings = QAction("Настройки сетки…", window)
        grid_settings.triggered.connect(lambda: _show_grid_settings(window))
        view_menu.addSeparator()
        view_menu.addAction(grid_settings)


def _show_grid_settings(window) -> None:
    from ordpaint.ui.grid_settings_dialog import GridSettingsDialog

    dialog = GridSettingsDialog(window, window.canvas.grid_size)
    if dialog.exec() == dialog.DialogCode.Accepted:
        value = dialog.grid_size()
        window.canvas.set_grid_size(value)
        if hasattr(window, "ui_state"):
            window.ui_state.grid_size = value
        if hasattr(window, "_save_ui_state"):
            window._save_ui_state()
