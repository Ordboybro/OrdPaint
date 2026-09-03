from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QActionGroup, QColor, QIcon, QKeySequence, QPainter, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView,
    QColorDialog,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ordpaint.core.document import Document
from ordpaint.core.history import History
from ordpaint.core.project import ProjectError, load_project, save_project
from ordpaint.core.tools import TOOL_INFO, Tool
from ordpaint.ui.canvas import Canvas


BLEND_MODES: tuple[tuple[str, QPainter.CompositionMode], ...] = (
    ("Обычный", QPainter.CompositionMode.CompositionMode_SourceOver),
    ("Умножение", QPainter.CompositionMode.CompositionMode_Multiply),
    ("Экран", QPainter.CompositionMode.CompositionMode_Screen),
    ("Перекрытие", QPainter.CompositionMode.CompositionMode_Overlay),
    ("Затемнение", QPainter.CompositionMode.CompositionMode_Darken),
    ("Осветление", QPainter.CompositionMode.CompositionMode_Lighten),
    ("Разница", QPainter.CompositionMode.CompositionMode_Difference),
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.document = Document()
        self.history = History()
        self.current_path: str | None = None
        self.dirty = False
        self.setWindowTitle("OrdPaint — Безымянный")
        self.resize(1500, 950)
        self._create_canvas()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_tools_dock()
        self._create_layers_dock()
        self._create_color_dock()
        self._create_statusbar()
        self._refresh_layers()
        self.setStyleSheet(self._style_sheet())

    def _create_canvas(self) -> None:
        self.canvas = Canvas(self.document)
        self.setCentralWidget(self.canvas)
        self._connect_canvas()

    def _connect_canvas(self) -> None:
        self.canvas.action_started.connect(self._push_history)
        self.canvas.zoom_changed.connect(self._update_zoom_labels)
        self.canvas.document_changed.connect(self._on_document_changed)
        self.canvas.cursor_position_changed.connect(self._update_cursor_position)
        self.canvas.color_picked.connect(self._set_color_from_canvas)

    def _update_cursor_position(self, point) -> None:
        if hasattr(self, "position_label"):
            self.position_label.setText(f"X: {point.x()}  Y: {point.y()}")

    def _update_zoom_labels(self, value: int) -> None:
        if hasattr(self, "zoom_label"):
            self.zoom_label.setText(f"{value}%")
        if hasattr(self, "zoom_status_label"):
            self.zoom_status_label.setText(f"{value}%")

    def _replace_document(self, document: Document) -> None:
        old = self.centralWidget()
        state = None
        if isinstance(old, Canvas):
            state = {
                "color": QColor(old.color),
                "brush_size": old.brush_size,
                "opacity": old.opacity,
                "tool": old.tool,
                "show_grid": old.show_grid,
                "show_rulers": old.show_rulers,
                "grid_size": old.grid_size,
            }
        self.document = document
        self.canvas = Canvas(self.document)
        if state:
            self.canvas.set_color(state["color"])
            self.canvas.set_brush_size(state["brush_size"])
            self.canvas.set_opacity(state["opacity"])
            self.canvas.set_show_grid(state["show_grid"])
            self.canvas.set_show_rulers(state["show_rulers"])
            self.canvas.set_grid_size(state["grid_size"])
            self.canvas.set_tool(state["tool"])
        self.setCentralWidget(self.canvas)
        self._connect_canvas()
        if old:
            old.deleteLater()
        if hasattr(self, "grid_action"):
            self.grid_action.setChecked(self.canvas.show_grid)
            self.rulers_action.setChecked(self.canvas.show_rulers)
        if hasattr(self, "size_spin"):
            self.size_spin.blockSignals(True)
            self.size_spin.setValue(self.canvas.brush_size)
            self.size_spin.blockSignals(False)
            self.size_slider.blockSignals(True)
            self.size_slider.setValue(self.canvas.brush_size)
            self.size_slider.blockSignals(False)
            self.opacity_slider.blockSignals(True)
            self.opacity_slider.setValue(self.canvas.opacity)
            self.opacity_slider.blockSignals(False)
            self.opacity_value.setText(f"{self.canvas.opacity}%")
            self._sync_color_sliders(self.canvas.color)
            self._update_color_button(self.canvas.color)
        self._refresh_layers()
        self._update_history_actions()
        if hasattr(self, "document_size_label"):
            self.document_size_label.setText(f"{self.document.width} × {self.document.height} px")
        self.canvas.update()

    def _create_actions(self) -> None:
        self.new_action = QAction("Новый", self, shortcut=QKeySequence.New, triggered=self.new_document)
        self.open_action = QAction("Открыть…", self, shortcut=QKeySequence.Open, triggered=self.open_project)
        self.import_action = QAction("Импортировать изображение…", self, triggered=self.open_image)
        self.save_action = QAction("Сохранить", self, shortcut=QKeySequence.Save, triggered=self.save_project)
        self.save_as_action = QAction(
            "Сохранить как…", self, shortcut=QKeySequence.SaveAs, triggered=self.save_project_as
        )
        self.export_action = QAction("Экспортировать изображение…", self, triggered=self.export_image)
        self.exit_action = QAction("Выход", self, shortcut=QKeySequence.Quit, triggered=self.close)

        self.undo_action = QAction("Отменить", self, shortcut=QKeySequence.Undo, triggered=self.undo)
        self.redo_action = QAction("Повторить", self, shortcut=QKeySequence.Redo, triggered=self.redo)
        self.copy_action = QAction("Копировать", self, shortcut=QKeySequence.Copy, triggered=self.canvas.copy_selection)
        self.cut_action = QAction("Вырезать", self, shortcut=QKeySequence.Cut, triggered=self.canvas.cut_selection)
        self.paste_action = QAction(
            "Вставить", self, shortcut=QKeySequence.Paste, triggered=self.canvas.paste_from_clipboard
        )
        self.delete_action = QAction(
            "Удалить", self, shortcut=QKeySequence.Delete, triggered=self.canvas.delete_selection
        )
        self.select_all_action = QAction(
            "Выделить всё", self, shortcut=QKeySequence.SelectAll, triggered=self.canvas.select_all
        )
        self.deselect_action = QAction("Снять выделение", self, shortcut="Ctrl+D", triggered=self.canvas.deselect)

        self.zoom_in_action = QAction("Увеличить", self, shortcut=QKeySequence.ZoomIn, triggered=self.canvas.zoom_in)
        self.zoom_out_action = QAction("Уменьшить", self, shortcut=QKeySequence.ZoomOut, triggered=self.canvas.zoom_out)
        self.reset_view_action = QAction("100%", self, shortcut="Ctrl+0", triggered=self.canvas.reset_view)
        self.fit_view_action = QAction(
            "По размеру окна", self, shortcut="Ctrl+Shift+0", triggered=self.canvas.fit_to_window
        )
        self.grid_action = QAction(
            "Сетка", self, checkable=True, shortcut="Ctrl+'", triggered=self.canvas.set_show_grid
        )
        self.rulers_action = QAction(
            "Линейки", self, checkable=True, shortcut="Ctrl+R", checked=True, triggered=self.canvas.set_show_rulers
        )

        self.tool_actions: dict[Tool, QAction] = {}
        group = QActionGroup(self)
        group.setExclusive(True)
        labels = {
            Tool.BRUSH: "Кисть",
            Tool.ERASER: "Ластик",
            Tool.LINE: "Линия",
            Tool.RECTANGLE: "Прямоугольник",
            Tool.ELLIPSE: "Эллипс",
            Tool.FILL: "Заливка",
            Tool.EYEDROPPER: "Пипетка",
            Tool.SELECT_RECT: "Выделение",
        }
        shortcuts = {
            Tool.BRUSH: "B",
            Tool.ERASER: "E",
            Tool.LINE: "L",
            Tool.RECTANGLE: "R",
            Tool.ELLIPSE: "O",
            Tool.FILL: "G",
            Tool.EYEDROPPER: "I",
            Tool.SELECT_RECT: "M",
        }
        for tool, label in labels.items():
            action = QAction(label, self, checkable=True, shortcut=shortcuts[tool])
            action.setChecked(tool == Tool.BRUSH)
            action.triggered.connect(lambda checked=False, value=tool: self.set_tool(value))
            group.addAction(action)
            self.tool_actions[tool] = action
        self._update_history_actions()

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addActions([self.new_action, self.open_action, self.import_action])
        file_menu.addSeparator()
        file_menu.addActions([self.save_action, self.save_as_action, self.export_action])
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        edit_menu = self.menuBar().addMenu("Правка")
        edit_menu.addActions([self.undo_action, self.redo_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.copy_action, self.cut_action, self.paste_action, self.delete_action])
        edit_menu.addSeparator()
        edit_menu.addActions([self.select_all_action, self.deselect_action])
        view_menu = self.menuBar().addMenu("Вид")
        view_menu.addActions(
            [
                self.zoom_in_action,
                self.zoom_out_action,
                self.reset_view_action,
                self.fit_view_action,
                self.grid_action,
                self.rulers_action,
            ]
        )
        image_menu = self.menuBar().addMenu("Изображение")
        image_menu.addAction(self.import_action)
        image_menu.addAction("Очистить активный слой", self.clear_active_layer)
        layer_menu = self.menuBar().addMenu("Слой")
        layer_menu.addActions(
            [
                QAction("Новый слой", self, shortcut="Ctrl+Shift+N", triggered=self.add_layer),
                QAction("Дублировать слой", self, shortcut="Ctrl+J", triggered=self.duplicate_layer),
                QAction("Удалить слой", self, triggered=self.remove_layer),
                QAction("Переместить вверх", self, shortcut="Ctrl+]", triggered=lambda: self.move_layer(1)),
                QAction("Переместить вниз", self, shortcut="Ctrl+[", triggered=lambda: self.move_layer(-1)),
                QAction("Объединить с нижним", self, shortcut="Ctrl+E", triggered=self.merge_layer_down),
                QAction("Объединить видимые", self, triggered=self.merge_visible_layers),
            ]
        )
        tools_menu = self.menuBar().addMenu("Инструменты")
        tools_menu.addActions(self.tool_actions.values())

    def _create_tool_button(self, action: QAction, text: str) -> QToolButton:
        button = QToolButton()
        button.setDefaultAction(action)
        button.setText(text)
        button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        button.setMinimumWidth(58)
        return button

    def _create_toolbars(self) -> None:
        file_bar = self.addToolBar("Файл")
        file_bar.setObjectName("fileToolbar")
        file_bar.setMovable(False)
        for action, glyph in (
            (self.new_action, "▣"),
            (self.open_action, "▰"),
            (self.save_action, "▣"),
            (self.export_action, "⇧"),
        ):
            button = self._create_tool_button(action, glyph)
            button.setToolTip(action.text())
            file_bar.addWidget(button)
        file_bar.addSeparator()
        for action, glyph in ((self.undo_action, "↶"), (self.redo_action, "↷")):
            button = self._create_tool_button(action, glyph)
            button.setToolTip(action.text())
            file_bar.addWidget(button)
        view_bar = self.addToolBar("Вид")
        view_bar.setObjectName("viewToolbar")
        view_bar.setMovable(False)
        view_bar.addWidget(QLabel("Масштаб"))
        self.zoom_label = QLabel("100%")
        self.zoom_label.setObjectName("zoomValue")
        view_bar.addWidget(self.zoom_label)
        for action, glyph, tip in (
            (self.fit_view_action, "⊙", "По размеру окна"),
            (self.reset_view_action, "100", "100%"),
        ):
            button = QToolButton()
            button.setDefaultAction(action)
            button.setText(glyph)
            button.setToolTip(tip)
            view_bar.addWidget(button)

    def _create_tools_dock(self) -> None:
        dock = QDockWidget("Инструменты", self)
        dock.setObjectName("toolsDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        widget = QWidget()
        widget.setObjectName("toolsPanel")
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        glyphs = {
            Tool.BRUSH: "╱",
            Tool.ERASER: "◇",
            Tool.LINE: "╲",
            Tool.RECTANGLE: "□",
            Tool.ELLIPSE: "○",
            Tool.FILL: "▾",
            Tool.EYEDROPPER: "⌖",
            Tool.SELECT_RECT: "⬚",
        }
        for index, tool in enumerate(TOOL_INFO):
            button = QToolButton()
            button.setDefaultAction(self.tool_actions[tool])
            button.setText(glyphs[tool])
            button.setObjectName("toolPaletteButton")
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            button.setFixedSize(42, 42)
            button.setToolTip(f"{TOOL_INFO[tool].label} ({TOOL_INFO[tool].shortcut})")
            grid.addWidget(button, index // 2, index % 2)
        layout.addLayout(grid)
        options_title = QLabel("Параметры")
        options_title.setObjectName("panelSectionTitle")
        layout.addWidget(options_title)
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Размер"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 500)
        self.size_spin.setValue(self.canvas.brush_size)
        self.size_spin.valueChanged.connect(self.canvas.set_brush_size)
        size_row.addWidget(self.size_spin)
        layout.addLayout(size_row)
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(1, 500)
        self.size_slider.setValue(self.canvas.brush_size)
        self.size_slider.valueChanged.connect(self.size_spin.setValue)
        self.size_spin.valueChanged.connect(self.size_slider.setValue)
        layout.addWidget(self.size_slider)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Непрозрачность"))
        self.opacity_value = QLabel("100%")
        self.opacity_value.setObjectName("valueLabel")
        opacity_row.addStretch()
        opacity_row.addWidget(self.opacity_value)
        layout.addLayout(opacity_row)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(1, 100)
        self.opacity_slider.setValue(self.canvas.opacity)
        self.opacity_slider.valueChanged.connect(self.canvas.set_opacity)
        self.opacity_slider.valueChanged.connect(lambda value: self.opacity_value.setText(f"{value}%"))
        layout.addWidget(self.opacity_slider)
        color_title = QLabel("Основной цвет")
        color_title.setObjectName("panelSectionTitle")
        layout.addWidget(color_title)
        self.color_button = QPushButton()
        self.color_button.setObjectName("primaryColorButton")
        self.color_button.setMinimumHeight(42)
        self.color_button.clicked.connect(self.choose_color)
        layout.addWidget(self.color_button)
        self._update_color_button(self.canvas.color)
        layout.addStretch(1)
        dock.setWidget(widget)
        self.tools_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)

    def _create_layers_dock(self) -> None:
        dock = QDockWidget("Слои", self)
        dock.setObjectName("layersDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.layers_list = QListWidget()
        self.layers_list.setObjectName("layersList")
        self.layers_list.setMinimumHeight(220)
        self.layers_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.layers_list.currentRowChanged.connect(self._set_active_layer)
        self.layers_list.itemChanged.connect(self._layer_item_changed)
        layout.addWidget(self.layers_list)
        controls = QHBoxLayout()
        for text_value, slot, tooltip in (
            ("+", self.add_layer, "Новый слой"),
            ("⧉", self.duplicate_layer, "Дублировать"),
            ("↑", lambda: self.move_layer(1), "Выше"),
            ("↓", lambda: self.move_layer(-1), "Ниже"),
            ("⌫", self.remove_layer, "Удалить"),
        ):
            button = QToolButton()
            button.setText(text_value)
            button.setToolTip(tooltip)
            button.setFixedSize(34, 30)
            button.clicked.connect(slot)
            controls.addWidget(button)
        layout.addLayout(controls)
        blend_row = QHBoxLayout()
        blend_row.addWidget(QLabel("Режим"))
        self.blend_mode_combo = QComboBox()
        for label, mode in BLEND_MODES:
            self.blend_mode_combo.addItem(label, mode)
        self.blend_mode_combo.currentIndexChanged.connect(self._set_active_layer_blend_mode)
        blend_row.addWidget(self.blend_mode_combo, 1)
        layout.addLayout(blend_row)
        opacity_row = QHBoxLayout()
        opacity_row.addWidget(QLabel("Непрозрачность"))
        self.layer_opacity_value = QLabel("100%")
        self.layer_opacity_value.setObjectName("valueLabel")
        opacity_row.addStretch()
        opacity_row.addWidget(self.layer_opacity_value)
        layout.addLayout(opacity_row)
        self.layer_opacity = QSlider(Qt.Orientation.Horizontal)
        self.layer_opacity.setRange(0, 100)
        self.layer_opacity.sliderPressed.connect(self._begin_layer_opacity_transaction)
        self.layer_opacity.valueChanged.connect(self._set_active_layer_opacity)
        self.layer_opacity.sliderReleased.connect(self._end_layer_opacity_transaction)
        layout.addWidget(self.layer_opacity)
        self.lock_button = QPushButton("🔒  Заблокировать слой")
        self.lock_button.setCheckable(True)
        self.lock_button.clicked.connect(self._toggle_active_layer_lock)
        layout.addWidget(self.lock_button)
        dock.setWidget(widget)
        self.layers_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_color_dock(self) -> None:
        dock = QDockWidget("Цвета", self)
        dock.setObjectName("colorDock")
        dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        self.foreground_preview = QPushButton()
        self.foreground_preview.setObjectName("foregroundPreview")
        self.foreground_preview.setFixedHeight(54)
        self.foreground_preview.clicked.connect(self.choose_color)
        layout.addWidget(self.foreground_preview)
        for title, channel in (("R", "red"), ("G", "green"), ("B", "blue")):
            row = QHBoxLayout()
            row.addWidget(QLabel(title))
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 255)
            slider.valueChanged.connect(self._sliders_to_color)
            row.addWidget(slider)
            layout.addLayout(row)
            setattr(self, f"{channel}_slider", slider)
        palette_title = QLabel("Быстрые цвета")
        palette_title.setObjectName("panelSectionTitle")
        layout.addWidget(palette_title)
        swatches = QGridLayout()
        for index, color in enumerate(
            ["#ff6b00", "#f4f4f4", "#9da9b5", "#4f8fe8", "#26384d", "#0f1115", "#d14b4b", "#5fb878"]
        ):
            button = QPushButton()
            button.setObjectName("swatch")
            button.setFixedSize(26, 26)
            button.setStyleSheet(f"QPushButton {{ background: {color}; }}")
            button.clicked.connect(lambda checked=False, value=color: self._set_color_from_canvas(QColor(value)))
            swatches.addWidget(button, index // 4, index % 4)
        layout.addLayout(swatches)
        layout.addStretch(1)
        self._sync_color_sliders(self.canvas.color)
        dock.setWidget(widget)
        self.color_dock = dock
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self.splitDockWidget(self.layers_dock, self.color_dock, Qt.Orientation.Vertical)

    def _create_statusbar(self) -> None:
        self.document_size_label = QLabel(f"{self.document.width} × {self.document.height} px")
        self.position_label = QLabel("X: —   Y: —")
        self.zoom_status_label = QLabel("100%")
        self.layer_status_label = QLabel(self.document.active_layer.name)
        status = self.statusBar()
        status.addWidget(self.document_size_label)
        status.addWidget(QLabel("   "))
        status.addWidget(self.position_label)
        status.addPermanentWidget(self.layer_status_label)
        status.addPermanentWidget(self.zoom_status_label)
        status.showMessage("Готово")

    def _push_history(self) -> None:
        self.history.push(self.document)
        self._update_history_actions()

    def _on_document_changed(self) -> None:
        self.dirty = True
        self._refresh_layers()
        self._update_history_actions()
        self.canvas.update()
        self._update_window_title()

    def _update_window_title(self) -> None:
        name = Path(self.current_path).name if self.current_path else "Безымянный"
        marker = " •" if self.dirty else ""
        self.setWindowTitle(f"OrdPaint — {name}{marker}")

    def undo(self) -> None:
        document = self.history.undo(self.document)
        if document is None:
            return
        self._replace_document(document)
        self.dirty = self.history.is_dirty()
        self._update_window_title()
        self._update_history_actions()

    def redo(self) -> None:
        document = self.history.redo(self.document)
        if document is None:
            return
        self._replace_document(document)
        self.dirty = self.history.is_dirty()
        self._update_window_title()
        self._update_history_actions()

    def _update_history_actions(self) -> None:
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(self.history.can_undo())
            self.redo_action.setEnabled(self.history.can_redo())

    def set_tool(self, tool: Tool) -> None:
        self.canvas.set_tool(tool)
        self.statusBar().showMessage(f"Инструмент: {self.tool_actions[tool].text()}", 1500)

    def _refresh_layers(self) -> None:
        if not hasattr(self, "layers_list"):
            return
        self.layers_list.blockSignals(True)
        self.layers_list.clear()
        for layer in reversed(self.document.layers):
            thumbnail = layer.pixmap.scaled(
                38, 38, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            item = QListWidgetItem(QIcon(thumbnail), layer.name)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            item.setToolTip("Заблокирован" if layer.locked else "Двойной клик для переименования")
            self.layers_list.addItem(item)
        row = len(self.document.layers) - 1 - self.document.active_index
        self.layers_list.setCurrentRow(row)
        self.layers_list.blockSignals(False)
        if hasattr(self, "layer_opacity"):
            layer = self.document.active_layer
            self.layer_opacity.blockSignals(True)
            self.layer_opacity.setValue(layer.opacity)
            self.layer_opacity.blockSignals(False)
            self.layer_opacity_value.setText(f"{layer.opacity}%")
            self.lock_button.blockSignals(True)
            self.lock_button.setChecked(layer.locked)
            self.lock_button.setText("🔒  Слой заблокирован" if layer.locked else "🔓  Заблокировать слой")
            self.lock_button.blockSignals(False)
            self.blend_mode_combo.blockSignals(True)
            for index in range(self.blend_mode_combo.count()):
                if self.blend_mode_combo.itemData(index) == layer.blend_mode:
                    self.blend_mode_combo.setCurrentIndex(index)
                    break
            self.blend_mode_combo.blockSignals(False)
            if hasattr(self, "layer_status_label"):
                self.layer_status_label.setText(layer.name)

    def _set_active_layer(self, row: int) -> None:
        if row < 0 or row >= len(self.document.layers):
            return
        self.document.set_active_index(len(self.document.layers) - 1 - row)
        self._refresh_layers()
        self.canvas.update()

    def _layer_item_changed(self, item: QListWidgetItem) -> None:
        row = self.layers_list.row(item)
        if row < 0:
            return
        index = len(self.document.layers) - 1 - row
        layer = self.document.layers[index]
        new_visible = item.checkState() == Qt.CheckState.Checked
        if layer.visible != new_visible:
            self._push_history()
            self.document.set_layer_visibility(index, new_visible)
            self.dirty = True
            self._update_window_title()
            self.canvas.update()
        new_name = item.text().strip()
        if new_name and new_name != layer.name:
            self._push_history()
            self.document.rename_layer(index, new_name)
            self.dirty = True
            self._refresh_layers()
            self._update_window_title()

    def _begin_layer_opacity_transaction(self) -> None:
        self.history.begin_transaction(self.document)

    def _set_active_layer_opacity(self, value: int) -> None:
        layer = self.document.active_layer
        if layer.opacity == value:
            self.layer_opacity_value.setText(f"{value}%")
            return
        if not self.history.transaction_active():
            self.history.push(self.document)
        self.document.set_layer_opacity(self.document.active_index, value)
        self.layer_opacity_value.setText(f"{value}%")
        self.dirty = True
        self._update_window_title()
        self.canvas.update()

    def _end_layer_opacity_transaction(self) -> None:
        if self.history.end_transaction(self.document):
            self._update_history_actions()
        self._refresh_layers()

    def _set_active_layer_blend_mode(self, combo_index: int) -> None:
        if combo_index < 0:
            return
        mode = self.blend_mode_combo.itemData(combo_index)
        if not isinstance(mode, QPainter.CompositionMode):
            mode = QPainter.CompositionMode(mode)
        if self.document.active_layer.blend_mode == mode:
            return
        self._push_history()
        if self.document.set_layer_blend_mode(self.document.active_index, mode):
            self.dirty = True
            self._update_window_title()
            self.canvas.update()

    def _toggle_active_layer_lock(self, checked: bool) -> None:
        if self.document.active_layer.locked == checked:
            return
        self._push_history()
        self.document.set_layer_locked(self.document.active_index, checked)
        self.dirty = True
        self._update_window_title()
        self._refresh_layers()

    def add_layer(self) -> None:
        self._push_history()
        self.document.add_layer()
        self.dirty = True
        self._refresh_layers()
        self.canvas.update()
        self._update_window_title()

    def duplicate_layer(self) -> None:
        self._push_history()
        self.document.duplicate_active_layer()
        self.dirty = True
        self._refresh_layers()
        self.canvas.update()
        self._update_window_title()

    def remove_layer(self) -> None:
        if len(self.document.layers) <= 1:
            return
        self._push_history()
        self.document.remove_active_layer()
        self.dirty = True
        self._refresh_layers()
        self.canvas.update()
        self._update_window_title()

    def move_layer(self, offset: int) -> None:
        target = self.document.active_index + offset
        if not 0 <= target < len(self.document.layers):
            return
        self._push_history()
        self.document.move_active_layer(offset)
        self.dirty = True
        self._refresh_layers()
        self.canvas.update()
        self._update_window_title()

    def merge_layer_down(self) -> None:
        if self.document.active_index <= 0 or self.document.layers[self.document.active_index - 1].locked:
            return
        self._push_history()
        if self.document.merge_active_down():
            self.dirty = True
            self._refresh_layers()
            self.canvas.update()
            self._update_window_title()

    def merge_visible_layers(self) -> None:
        visible = [layer for layer in self.document.layers if layer.visible]
        if len(visible) <= 1 or visible[0].locked:
            return
        self._push_history()
        if self.document.merge_visible():
            self.dirty = True
            self._refresh_layers()
            self.canvas.update()
            self._update_window_title()

    def clear_active_layer(self) -> None:
        if self.document.active_layer.locked:
            return
        self._push_history()
        if self.document.clear_active_layer():
            self.dirty = True
            self.canvas.update()
            self._refresh_layers()
            self._update_window_title()

    def choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.color, self, "Выберите цвет")
        if color.isValid():
            self._set_color_from_canvas(color)

    def _set_color_from_canvas(self, color: QColor) -> None:
        self.canvas.set_color(color)
        self._sync_color_sliders(color)
        self._update_color_button(color)

    def _sync_color_sliders(self, color: QColor) -> None:
        if not hasattr(self, "red_slider"):
            return
        for slider, value in (
            (self.red_slider, color.red()),
            (self.green_slider, color.green()),
            (self.blue_slider, color.blue()),
        ):
            slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(False)
        self.foreground_preview.setStyleSheet(f"background: {color.name()};")

    def _sliders_to_color(self) -> None:
        self._set_color_from_canvas(
            QColor(self.red_slider.value(), self.green_slider.value(), self.blue_slider.value())
        )

    def _update_color_button(self, color: QColor) -> None:
        text_color = "#ffffff" if color.lightness() < 128 else "#111111"
        self.color_button.setText(color.name().upper())
        self.color_button.setStyleSheet(f"background:{color.name()}; color:{text_color}; border: 1px solid #4a4f59;")

    def new_document(self) -> None:
        if not self._confirm_discard():
            return
        self.history.clear()
        self.current_path = None
        self.dirty = False
        self._replace_document(Document())
        self.history.mark_saved()
        self._update_window_title()

    def open_project(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", "", "OrdPaint Project (*.ordpaint)")
        if not path:
            return
        try:
            document = load_project(path)
        except ProjectError as exc:
            QMessageBox.critical(self, "Не удалось открыть проект", str(exc))
            return
        self.history.clear()
        self.history.mark_saved()
        self.current_path = path
        self.dirty = False
        self._replace_document(document)
        self._update_window_title()

    def open_image(self) -> None:
        if not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Импортировать изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not path:
            return
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            return
        self.history.clear()
        document = Document(pixmap.width(), pixmap.height())
        document.active_layer.pixmap = pixmap
        document.touch()
        self.current_path = None
        self.dirty = True
        self._replace_document(document)
        self._update_window_title()

    def save_project(self) -> None:
        if self.current_path and self.current_path.lower().endswith(".ordpaint"):
            self._write_project(self.current_path)
        else:
            self.save_project_as()

    def save_project_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект", "", "OrdPaint Project (*.ordpaint)")
        if not path:
            return
        if not path.lower().endswith(".ordpaint"):
            path += ".ordpaint"
        self._write_project(path)

    def _write_project(self, path: str) -> None:
        try:
            save_project(self.document, path)
        except (OSError, ProjectError) as exc:
            QMessageBox.critical(self, "Ошибка сохранения", str(exc))
            return
        self.current_path = path
        self.history.mark_saved()
        self.dirty = False
        self.statusBar().showMessage("Проект сохранён", 3000)
        self._update_window_title()

    def export_image(self) -> None:
        path, selected_filter = QFileDialog.getSaveFileName(
            self, "Экспортировать изображение", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;WEBP (*.webp);;BMP (*.bmp)"
        )
        if not path:
            return
        suffixes = {
            "PNG (*.png)": ".png",
            "JPEG (*.jpg *.jpeg)": ".jpg",
            "WEBP (*.webp)": ".webp",
            "BMP (*.bmp)": ".bmp",
        }
        if not Path(path).suffix:
            path += suffixes.get(selected_filter, ".png")
        if not self.document.composite().save(path):
            QMessageBox.warning(self, "Ошибка", "Не удалось экспортировать изображение.")
            return
        self.statusBar().showMessage("Изображение экспортировано", 3000)

    def _confirm_discard(self) -> bool:
        if not self.dirty:
            return True
        result = QMessageBox.question(
            self,
            "Несохранённые изменения",
            "В документе есть несохранённые изменения. Продолжить без сохранения?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )
        if result == QMessageBox.StandardButton.Save:
            self.save_project()
            return not self.dirty
        return result == QMessageBox.StandardButton.Discard

    def closeEvent(self, event) -> None:
        if self._confirm_discard():
            event.accept()
        else:
            event.ignore()

    @staticmethod
    def _style_sheet() -> str:
        return """
        QMainWindow { background: #242424; color: #d9d9d9; }
        QMenuBar { background: #2b2b2b; border-bottom: 1px solid #3a3a3a; color: #d8d8d8; padding: 2px 8px; }
        QMenuBar::item { padding: 6px 10px; border-radius: 3px; }
        QMenuBar::item:selected { background: #3b3b3b; }
        QMenu { background: #2c2c2c; border: 1px solid #474747; color: #e5e5e5; padding: 5px; }
        QMenu::item { padding: 7px 28px 7px 12px; border-radius: 3px; }
        QMenu::item:selected { background: #4a321b; }
        QToolBar { background: #303030; border: none; border-bottom: 1px solid #444; spacing: 4px; padding: 4px 8px; }
        QToolBar::separator { width: 1px; background: #4a4a4a; margin: 4px 7px; }
        QToolButton { color: #d8d8d8; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: 4px; }
        QToolButton:hover { background: #3b3b3b; border-color: #555; }
        QToolButton:checked { background: #4b3218; border-color: #d8892d; color: #ffb65a; }
        QDockWidget { background: #292929; color: #e0e0e0; border: 1px solid #3c3c3c; }
        QDockWidget::title { background: #303030; padding: 8px 10px; text-align: left; font-weight: 700; border-bottom: 1px solid #404040; }
        QWidget#toolsPanel, QDockWidget > QWidget { background: #292929; }
        QLabel#panelSectionTitle { color: #aaa; font-size: 11px; font-weight: 700; margin-top: 6px; }
        QLabel#valueLabel, QLabel#zoomValue { color: #f0a24a; font-weight: 700; }
        QToolButton#toolPaletteButton { font-size: 22px; background: #303030; border: 1px solid #444; border-radius: 5px; }
        QToolButton#toolPaletteButton:hover { background: #3c3c3c; }
        QToolButton#toolPaletteButton:checked { background: #4b3218; border-color: #d8892d; color: #ffbd69; }
        QListWidget { background: #232323; border: 1px solid #444; border-radius: 4px; color: #e2e2e2; outline: none; }
        QListWidget::item { min-height: 42px; padding: 4px; border-bottom: 1px solid #303030; }
        QListWidget::item:selected { background: #4b3218; color: #fff1dc; }
        QPushButton, QSpinBox, QComboBox { background: #333; border: 1px solid #494949; border-radius: 4px; color: #e7e7e7; padding: 6px 9px; }
        QPushButton:hover, QSpinBox:hover, QComboBox:hover { background: #3d3d3d; border-color: #5b5b5b; }
        QPushButton:checked { background: #4b3218; border-color: #d8892d; }
        QComboBox QAbstractItemView { background: #333; color: #e7e7e7; selection-background-color: #4b3218; }
        QPushButton#primaryColorButton, QPushButton#foregroundPreview { border-radius: 5px; }
        QSlider::groove:horizontal { height: 4px; background: #4a4a4a; border-radius: 2px; }
        QSlider::sub-page:horizontal { background: #c9782b; border-radius: 2px; }
        QSlider::handle:horizontal { width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; background: #f0a24a; }
        QStatusBar { background: #303030; border-top: 1px solid #444; color: #aaa; }
        QMainWindow::separator { background: #444; width: 1px; height: 1px; }
        """
