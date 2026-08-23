from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QPixmap
from PySide6.QtWidgets import QColorDialog, QDockWidget, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QSlider, QSpinBox, QToolButton, QVBoxLayout, QWidget

from ordpaint.core.document import Document
from ordpaint.core.history import History
from ordpaint.core.tools import Tool
from ordpaint.ui.canvas import Canvas


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__(); self.document = Document(); self.history = History(); self.current_path: str | None = None
        self.setWindowTitle("OrdPaint — Untitled"); self.resize(1500, 950)
        self._create_canvas(); self._create_actions(); self._create_menus(); self._create_toolbars(); self._create_layers_dock(); self._create_color_dock(); self._create_statusbar(); self._refresh_layers(); self.setStyleSheet(self._style_sheet())

    def _create_canvas(self) -> None:
        self.canvas = Canvas(self.document); self.setCentralWidget(self.canvas); self._connect_canvas()

    def _connect_canvas(self) -> None:
        self.canvas.action_started.connect(self._push_history)
        self.canvas.zoom_changed.connect(lambda value: self.zoom_label.setText(f"{value}%") if hasattr(self, "zoom_label") else None)
        self.canvas.document_changed.connect(self._on_document_changed)
        self.canvas.cursor_position_changed.connect(lambda p: self.position_label.setText(f"X: {p.x()}  Y: {p.y()}"))
        self.canvas.color_picked.connect(self._set_color_from_canvas)

    def _replace_document(self, document: Document) -> None:
        self.document = document; old = self.centralWidget(); self.canvas = Canvas(self.document); self.setCentralWidget(self.canvas); self._connect_canvas()
        if old: old.deleteLater()
        self._refresh_layers(); self._update_history_actions()

    def _create_actions(self) -> None:
        self.new_action = QAction("Новый", self, shortcut=QKeySequence.New, triggered=self.new_document); self.open_action = QAction("Открыть", self, shortcut=QKeySequence.Open, triggered=self.open_image); self.save_action = QAction("Сохранить", self, shortcut=QKeySequence.Save, triggered=self.save_image); self.save_as_action = QAction("Сохранить как…", self, shortcut=QKeySequence.SaveAs, triggered=lambda: self.save_image(save_as=True)); self.exit_action = QAction("Выход", self, shortcut=QKeySequence.Quit, triggered=self.close)
        self.undo_action = QAction("Отменить", self, shortcut=QKeySequence.Undo, triggered=self.undo); self.redo_action = QAction("Повторить", self, shortcut=QKeySequence.Redo, triggered=self.redo); self.zoom_in_action = QAction("Увеличить", self, shortcut=QKeySequence.ZoomIn, triggered=self.canvas.zoom_in); self.zoom_out_action = QAction("Уменьшить", self, shortcut=QKeySequence.ZoomOut, triggered=self.canvas.zoom_out); self.reset_view_action = QAction("100%", self, shortcut="Ctrl+0", triggered=self.canvas.reset_view); self.fit_view_action = QAction("По размеру окна", self, shortcut="Ctrl+Shift+0", triggered=self.canvas.fit_to_window)
        self.tool_actions = {}; group = QActionGroup(self); group.setExclusive(True)
        labels = {Tool.BRUSH: "Кисть", Tool.ERASER: "Ластик", Tool.LINE: "Линия", Tool.RECTANGLE: "Прямоугольник", Tool.ELLIPSE: "Эллипс", Tool.FILL: "Заливка", Tool.EYEDROPPER: "Пипетка", Tool.SELECT_RECT: "Выделение"}; shortcuts = {Tool.BRUSH: "B", Tool.ERASER: "E", Tool.LINE: "L", Tool.RECTANGLE: "R", Tool.ELLIPSE: "O", Tool.FILL: "G", Tool.EYEDROPPER: "I", Tool.SELECT_RECT: "M"}
        for tool, label in labels.items():
            action = QAction(label, self, checkable=True, shortcut=shortcuts[tool]); action.setChecked(tool == Tool.BRUSH); action.triggered.connect(lambda checked=False, value=tool: self.set_tool(value)); group.addAction(action); self.tool_actions[tool] = action
        self._update_history_actions()

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("Файл"); file_menu.addActions([self.new_action, self.open_action, self.save_action, self.save_as_action]); file_menu.addSeparator(); file_menu.addAction(self.exit_action)
        edit_menu = self.menuBar().addMenu("Правка"); edit_menu.addActions([self.undo_action, self.redo_action]); tools_menu = self.menuBar().addMenu("Инструменты"); tools_menu.addActions(self.tool_actions.values()); view_menu = self.menuBar().addMenu("Вид"); view_menu.addActions([self.zoom_in_action, self.zoom_out_action, self.reset_view_action, self.fit_view_action])

    def _create_tool_button(self, action: QAction, text: str) -> QToolButton:
        button = QToolButton(); button.setDefaultAction(action); button.setText(text); button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon); button.setMinimumWidth(58); return button

    def _create_toolbars(self) -> None:
        tool_bar = self.addToolBar("Инструменты"); tool_bar.setMovable(False)
        for tool, text in [(Tool.BRUSH, "Кисть"), (Tool.ERASER, "Ластик"), (Tool.LINE, "Линия"), (Tool.RECTANGLE, "Прям."), (Tool.ELLIPSE, "Эллипс"), (Tool.FILL, "Заливка"), (Tool.EYEDROPPER, "Пипетка"), (Tool.SELECT_RECT, "Выдел.")]: tool_bar.addWidget(self._create_tool_button(self.tool_actions[tool], text))
        options = self.addToolBar("Параметры"); options.setMovable(False); options.addWidget(QLabel(" Размер: ")); self.size_spin = QSpinBox(); self.size_spin.setRange(1, 500); self.size_spin.setValue(self.canvas.brush_size); self.size_spin.valueChanged.connect(self.canvas.set_brush_size); options.addWidget(self.size_spin); options.addWidget(QLabel("  Непрозрачность: ")); self.opacity_slider = QSlider(Qt.Orientation.Horizontal); self.opacity_slider.setRange(1, 100); self.opacity_slider.setValue(100); self.opacity_slider.setFixedWidth(140); self.opacity_slider.valueChanged.connect(self.canvas.set_opacity); options.addWidget(self.opacity_slider); self.color_button = QPushButton("#111111"); self.color_button.clicked.connect(self.choose_color); options.addWidget(self.color_button); self._update_color_button(self.canvas.color); options.addSeparator(); self.zoom_label = QLabel("100%"); options.addWidget(self.zoom_label)

    def _create_layers_dock(self) -> None:
        dock = QDockWidget("Слои", self); dock.setMinimumWidth(250); widget = QWidget(); layout = QVBoxLayout(widget); layout.setContentsMargins(8, 8, 8, 8); self.layers_list = QListWidget(); self.layers_list.currentRowChanged.connect(self._set_active_layer); self.layers_list.itemChanged.connect(self._change_layer_visibility); layout.addWidget(self.layers_list); row = QHBoxLayout()
        for text, slot in [("+", self.add_layer), ("⧉", self.duplicate_layer), ("−", self.remove_layer)]: button = QPushButton(text); button.setFixedWidth(60); button.clicked.connect(slot); row.addWidget(button)
        layout.addLayout(row); dock.setWidget(widget); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_color_dock(self) -> None:
        dock = QDockWidget("Цвет", self); widget = QWidget(); layout = QVBoxLayout(widget); self.foreground_preview = QPushButton(); self.foreground_preview.setFixedHeight(44); self.foreground_preview.clicked.connect(self.choose_color); layout.addWidget(self.foreground_preview); self.red_slider = QSlider(Qt.Orientation.Horizontal); self.green_slider = QSlider(Qt.Orientation.Horizontal); self.blue_slider = QSlider(Qt.Orientation.Horizontal)
        for slider in (self.red_slider, self.green_slider, self.blue_slider): slider.setRange(0, 255); slider.valueChanged.connect(self._sliders_to_color); layout.addWidget(slider)
        self._sync_color_sliders(self.canvas.color); dock.setWidget(widget); self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_statusbar(self) -> None:
        self.position_label = QLabel("X: —  Y: —"); self.statusBar().addPermanentWidget(self.position_label); self.statusBar().showMessage("Готово")

    def _push_history(self) -> None: self.history.push(self.document); self._update_history_actions()
    def _on_document_changed(self) -> None: self._refresh_layers(); self.canvas.update(); self.setWindowTitle("OrdPaint — *")

    def undo(self) -> None:
        document = self.history.undo(self.document)
        if document: self._replace_document(document)

    def redo(self) -> None:
        document = self.history.redo(self.document)
        if document: self._replace_document(document)

    def _update_history_actions(self) -> None:
        if hasattr(self, "undo_action"): self.undo_action.setEnabled(self.history.can_undo()); self.redo_action.setEnabled(self.history.can_redo())

    def set_tool(self, tool: Tool) -> None: self.canvas.set_tool(tool); self.statusBar().showMessage(f"Инструмент: {self.tool_actions[tool].text()}", 1500)

    def _refresh_layers(self) -> None:
        if not hasattr(self, "layers_list"): return
        self.layers_list.blockSignals(True); self.layers_list.clear()
        for layer in reversed(self.document.layers): item = QListWidgetItem(layer.name); item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked); self.layers_list.addItem(item)
        self.layers_list.setCurrentRow(len(self.document.layers) - 1 - self.document.active_index); self.layers_list.blockSignals(False)

    def _set_active_layer(self, row: int) -> None:
        if row >= 0: self.document.active_index = len(self.document.layers) - 1 - row

    def _change_layer_visibility(self, item: QListWidgetItem) -> None:
        row = self.layers_list.row(item); index = len(self.document.layers) - 1 - row; self._push_history(); self.document.layers[index].visible = item.checkState() == Qt.CheckState.Checked; self.canvas.update()

    def add_layer(self) -> None: self._push_history(); self.document.add_layer(); self._refresh_layers(); self.canvas.update()
    def duplicate_layer(self) -> None: self._push_history(); self.document.duplicate_active_layer(); self._refresh_layers(); self.canvas.update()
    def remove_layer(self) -> None:
        if len(self.document.layers) > 1: self._push_history(); self.document.remove_active_layer(); self._refresh_layers(); self.canvas.update()

    def choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.color, self, "Выберите цвет")
        if color.isValid(): self._set_color_from_canvas(color)

    def _set_color_from_canvas(self, color: QColor) -> None: self.canvas.set_color(color); self._sync_color_sliders(color); self._update_color_button(color)

    def _sync_color_sliders(self, color: QColor) -> None:
        for slider, value in ((self.red_slider, color.red()), (self.green_slider, color.green()), (self.blue_slider, color.blue())): slider.blockSignals(True); slider.setValue(value); slider.blockSignals(False)
        self.foreground_preview.setStyleSheet(f"background: {color.name()};")

    def _sliders_to_color(self) -> None: self._set_color_from_canvas(QColor(self.red_slider.value(), self.green_slider.value(), self.blue_slider.value()))
    def _update_color_button(self, color: QColor) -> None: self.color_button.setText(color.name()); self.color_button.setStyleSheet(f"background:{color.name()}; color:{'#ffffff' if color.lightness() < 128 else '#111111'};")

    def new_document(self) -> None: self.history.clear(); self.current_path = None; self._replace_document(Document()); self.setWindowTitle("OrdPaint — Untitled")

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path: return
        pixmap = QPixmap(path)
        if pixmap.isNull(): return
        self.history.clear(); document = Document(pixmap.width(), pixmap.height()); document.active_layer.pixmap = pixmap; self.current_path = path; self._replace_document(document); self.setWindowTitle(f"OrdPaint — {path}")

    def save_image(self, save_as: bool = False) -> None:
        path = None if save_as else self.current_path
        if not path: path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;WEBP (*.webp);;BMP (*.bmp)")
        if not path: return
        if self.document.composite().save(path): self.current_path = path; self.statusBar().showMessage("Сохранено", 3000); self.setWindowTitle(f"OrdPaint — {path}")

    @staticmethod
    def _style_sheet() -> str:
        return """QMainWindow { background: #1e1f22; color: #d7d7d7; } QMenuBar, QMenu, QStatusBar { background: #26272b; color: #d7d7d7; } QMenu::item:selected { background: #3c4048; } QToolBar { background: #2a2b30; border: none; spacing: 4px; padding: 4px; } QToolButton { color: #d7d7d7; background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 5px; } QToolButton:hover, QToolButton:checked { background: #3d4f66; border-color: #5d83ad; } QDockWidget::title { background: #2a2b30; padding: 7px; font-weight: 700; } QListWidget { background: #25262a; border: 1px solid #3c3d42; color: #dedede; } QListWidget::item:selected { background: #394d64; } QPushButton, QSpinBox { background: #34363c; border: 1px solid #4b4d54; border-radius: 5px; color: #eeeeee; padding: 6px 9px; } QPushButton:hover { background: #44474f; } QSlider::groove:horizontal { height: 4px; background: #4b4d54; border-radius: 2px; } QSlider::handle:horizontal { width: 12px; margin: -4px 0; border-radius: 6px; background: #63a4ff; }"""
