from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QColor, QKeySequence
from PySide6.QtWidgets import (
    QColorDialog,
    QDockWidget,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
)

from ordpaint.core.document import Document
from ordpaint.ui.canvas import Canvas


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.document = Document()
        self.current_path: str | None = None
        self.setWindowTitle("OrdPaint")
        self.resize(1500, 950)
        self._create_canvas()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_layers_dock()
        self._create_statusbar()
        self._refresh_layers()
        self.setStyleSheet(self._style_sheet())

    def _create_canvas(self) -> None:
        self.canvas = Canvas(self.document)
        self.setCentralWidget(self.canvas)
        self.canvas.zoom_changed.connect(lambda value: self.zoom_label.setText(f"{value}%") if hasattr(self, "zoom_label") else None)
        self.canvas.document_changed.connect(self._refresh_layers)

    def _create_actions(self) -> None:
        self.new_action = QAction("Новый", self, shortcut=QKeySequence.New, triggered=self.new_document)
        self.open_action = QAction("Открыть", self, shortcut=QKeySequence.Open, triggered=self.open_image)
        self.save_action = QAction("Сохранить", self, shortcut=QKeySequence.Save, triggered=self.save_image)
        self.save_as_action = QAction("Сохранить как…", self, shortcut=QKeySequence.SaveAs, triggered=lambda: self.save_image(save_as=True))
        self.exit_action = QAction("Выход", self, shortcut=QKeySequence.Quit, triggered=self.close)
        self.undo_action = QAction("Отменить", self, shortcut=QKeySequence.Undo, enabled=False)
        self.redo_action = QAction("Повторить", self, shortcut=QKeySequence.Redo, enabled=False)
        self.brush_action = QAction("Кисть", self, checkable=True, checked=True)
        self.eraser_action = QAction("Ластик", self, checkable=True, triggered=self._toggle_eraser)
        self.zoom_in_action = QAction("Увеличить", self, shortcut=QKeySequence.ZoomIn, triggered=self.canvas.zoom_in)
        self.zoom_out_action = QAction("Уменьшить", self, shortcut=QKeySequence.ZoomOut, triggered=self.canvas.zoom_out)
        self.reset_view_action = QAction("100%", self, shortcut="Ctrl+0", triggered=self.canvas.reset_view)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("Файл")
        file_menu.addActions([self.new_action, self.open_action, self.save_action, self.save_as_action])
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        edit_menu = self.menuBar().addMenu("Правка")
        edit_menu.addActions([self.undo_action, self.redo_action])

        view_menu = self.menuBar().addMenu("Вид")
        view_menu.addActions([self.zoom_in_action, self.zoom_out_action, self.reset_view_action])

    def _create_toolbars(self) -> None:
        bar = self.addToolBar("Инструменты")
        bar.setMovable(False)
        bar.addAction(self.brush_action)
        bar.addAction(self.eraser_action)
        bar.addSeparator()
        bar.addWidget(QLabel(" Размер: "))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(1, 500)
        self.size_spin.setValue(self.canvas.brush_size)
        self.size_spin.valueChanged.connect(self.canvas.set_brush_size)
        bar.addWidget(self.size_spin)
        bar.addWidget(QLabel("  Непрозрачность: "))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(1, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setFixedWidth(140)
        self.opacity_slider.valueChanged.connect(self.canvas.set_opacity)
        bar.addWidget(self.opacity_slider)
        self.color_button = QPushButton("Цвет")
        self.color_button.clicked.connect(self.choose_color)
        bar.addWidget(self.color_button)
        bar.addSeparator()
        self.zoom_label = QLabel("100%")
        bar.addWidget(self.zoom_label)

    def _create_layers_dock(self) -> None:
        dock = QDockWidget("Слои", self)
        dock.setMinimumWidth(240)
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.layers_list = QListWidget()
        self.layers_list.currentRowChanged.connect(self._set_active_layer)
        layout.addWidget(self.layers_list)
        row = QHBoxLayout()
        add_button = QPushButton("+")
        remove_button = QPushButton("−")
        add_button.clicked.connect(self.add_layer)
        remove_button.clicked.connect(self.remove_layer)
        row.addWidget(add_button)
        row.addWidget(remove_button)
        layout.addLayout(row)
        dock.setWidget(widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)

    def _create_statusbar(self) -> None:
        self.statusBar().showMessage("Готово")

    def _refresh_layers(self) -> None:
        if not hasattr(self, "layers_list"):
            return
        self.layers_list.blockSignals(True)
        self.layers_list.clear()
        for layer in reversed(self.document.layers):
            item = QListWidgetItem(layer.name)
            item.setCheckState(Qt.CheckState.Checked if layer.visible else Qt.CheckState.Unchecked)
            self.layers_list.addItem(item)
        row = len(self.document.layers) - 1 - self.document.active_index
        self.layers_list.setCurrentRow(row)
        self.layers_list.blockSignals(False)

    def _set_active_layer(self, row: int) -> None:
        if row < 0:
            return
        self.document.active_index = len(self.document.layers) - 1 - row

    def add_layer(self) -> None:
        self.document.add_layer()
        self._refresh_layers()
        self.canvas.update()

    def remove_layer(self) -> None:
        if self.document.remove_active_layer():
            self._refresh_layers()
            self.canvas.update()

    def choose_color(self) -> None:
        color = QColorDialog.getColor(self.canvas.color, self, "Выберите цвет")
        if color.isValid():
            self.canvas.set_color(color)
            self.color_button.setStyleSheet(f"background: {color.name()}; color: {'white' if color.lightness() < 128 else 'black'}")

    def _toggle_eraser(self, checked: bool) -> None:
        self.canvas.set_eraser(checked)
        self.brush_action.setChecked(not checked)

    def new_document(self) -> None:
        self.document = Document()
        self.current_path = None
        self.setWindowTitle("OrdPaint — Новый файл")
        self.setCentralWidget(Canvas(self.document))
        self.canvas = self.centralWidget()
        self.canvas.zoom_changed.connect(lambda value: self.zoom_label.setText(f"{value}%"))
        self.canvas.document_changed.connect(self._refresh_layers)
        self._refresh_layers()

    def open_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Открыть изображение", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not path:
            return
        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return
        self.document = Document(pixmap.width(), pixmap.height())
        self.document.active_layer.pixmap = pixmap
        self.current_path = path
        self.setWindowTitle(f"OrdPaint — {path}")
        self.setCentralWidget(Canvas(self.document))
        self.canvas = self.centralWidget()
        self.canvas.zoom_changed.connect(lambda value: self.zoom_label.setText(f"{value}%"))
        self.canvas.document_changed.connect(self._refresh_layers)
        self._refresh_layers()

    def save_image(self, save_as: bool = False) -> None:
        path = None if save_as else self.current_path
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Сохранить изображение", "", "PNG (*.png);;JPEG (*.jpg *.jpeg);;WEBP (*.webp);;BMP (*.bmp)")
        if not path:
            return
        self.document.composite().save(path)
        self.current_path = path
        self.statusBar().showMessage("Сохранено", 3000)

    @staticmethod
    def _style_sheet() -> str:
        return """
        QMainWindow { background: #242424; color: #dddddd; }
        QMenuBar, QMenu { background: #2d2d2d; color: #dddddd; }
        QMenu::item:selected { background: #444444; }
        QToolBar { background: #303030; border: none; spacing: 6px; padding: 6px; }
        QDockWidget { color: #dddddd; font-weight: 600; }
        QListWidget { background: #303030; border: 1px solid #444444; color: #dddddd; }
        QPushButton, QSpinBox { background: #3a3a3a; border: 1px solid #555555; border-radius: 4px; color: #eeeeee; padding: 5px 8px; }
        QPushButton:hover { background: #4a4a4a; }
        QStatusBar { background: #2d2d2d; color: #bbbbbb; }
        """
