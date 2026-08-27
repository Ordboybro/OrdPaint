from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QAbstractItemView, QMenu, QMessageBox

from ordpaint.core.document import Document
from ordpaint.core.session import SessionManager
from ordpaint.core.ui_state import UIState
from ordpaint.ui.layer_list import LayerListWidget
from ordpaint.ui.main_window import MainWindow as BaseMainWindow
from ordpaint.ui.settings_store import SettingsStore


class MainWindow(BaseMainWindow):
    """Production integration layer for persistent UI and session workflows.

    The base window owns editor controls; this subclass wires the already-tested
    core services into the actual Qt application without moving persistence or
    recovery logic into widgets.
    """

    AUTOSAVE_INTERVAL_MS = 30_000

    def __init__(self) -> None:
        super().__init__()
        self.settings_store = SettingsStore()
        self.ui_state = self.settings_store.load()
        self.session = SessionManager()
        self.session.restore_recent(self.ui_state.recent_paths)

        self._install_layer_list()
        self._install_context_menu()
        self._install_transform_actions()
        self._install_recent_menu()
        self._rewire_file_actions()
        self._apply_ui_state(self.ui_state)

        self.autosave_timer = QTimer(self)
        self.autosave_timer.setInterval(self.AUTOSAVE_INTERVAL_MS)
        self.autosave_timer.timeout.connect(self._autosave_tick)
        self.autosave_timer.start()
        QTimer.singleShot(0, self._offer_recovery)

    def _rewire_file_actions(self) -> None:
        self.new_action.triggered.disconnect()
        self.open_action.triggered.disconnect()
        self.import_action.triggered.disconnect()
        self.save_action.triggered.disconnect()
        self.save_as_action.triggered.disconnect()
        self.new_action.triggered.connect(self.new_document)
        self.open_action.triggered.connect(self.open_project)
        self.import_action.triggered.connect(self.open_image)
        self.save_action.triggered.connect(self.save_project)
        self.save_as_action.triggered.connect(self.save_project_as)

    def _install_layer_list(self) -> None:
        old_list = self.layers_list
        layout = old_list.parentWidget().layout()
        new_list = LayerListWidget(old_list.parentWidget())
        new_list.setObjectName("layersList")
        new_list.setMinimumHeight(220)
        new_list.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        layout.replaceWidget(old_list, new_list)
        old_list.deleteLater()
        self.layers_list = new_list
        self.layers_list.currentRowChanged.connect(self._set_active_layer)
        self.layers_list.itemChanged.connect(self._layer_item_changed)
        self.layers_list.reorder_requested.connect(self._reorder_layers)
        self._refresh_layers()

    def _install_context_menu(self) -> None:
        self.layers_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.layers_list.customContextMenuRequested.connect(self._show_layer_context_menu)

    def _show_layer_context_menu(self, position) -> None:
        row = self.layers_list.indexAt(position).row()
        if row >= 0:
            self.layers_list.setCurrentRow(row)
        menu = QMenu(self.layers_list)
        menu.addAction("Новый слой", self.add_layer)
        menu.addAction("Дублировать", self.duplicate_layer)
        menu.addSeparator()
        menu.addAction("Переименовать", self._rename_current_layer)
        menu.addAction("Удалить", self.remove_layer)
        menu.addSeparator()
        menu.addAction("Выше", lambda: self.move_layer(1))
        menu.addAction("Ниже", lambda: self.move_layer(-1))
        menu.addSeparator()
        menu.addAction("Объединить с нижним", self.merge_layer_down)
        menu.addAction("Объединить видимые", self.merge_visible_layers)
        menu.exec(self.layers_list.viewport().mapToGlobal(position))

    def _rename_current_layer(self) -> None:
        item = self.layers_list.currentItem()
        if item is not None:
            self.layers_list.editItem(item)

    def _reorder_layers(self, source_row: int, target_row: int) -> None:
        count = len(self.document.layers)
        source_index = count - 1 - source_row
        target_index = count - 1 - target_row
        if source_index == target_index:
            self._refresh_layers()
            return
        self._push_history()
        if self.document.move_layer(source_index, target_index):
            self.dirty = True
            self._update_window_title()
            self.canvas.update()
        self._refresh_layers()

    def _install_transform_actions(self) -> None:
        self.begin_transform_action = QAction("Свободное трансформирование", self, shortcut="Ctrl+T")
        self.begin_transform_action.triggered.connect(self.canvas.begin_transform)
        self.commit_transform_action = QAction("Применить трансформацию", self, shortcut="Return")
        self.commit_transform_action.triggered.connect(self.canvas.commit_transform)
        self.cancel_transform_action = QAction("Отменить трансформацию", self, shortcut="Escape")
        self.cancel_transform_action.triggered.connect(self.canvas.cancel_transform)
        self.flip_horizontal_action = QAction("Отразить по горизонтали", self)
        self.flip_horizontal_action.triggered.connect(self.canvas.flip_transform_horizontal)
        self.flip_vertical_action = QAction("Отразить по вертикали", self)
        self.flip_vertical_action.triggered.connect(self.canvas.flip_transform_vertical)
        self.rotate_clockwise_action = QAction("Повернуть на 90° вправо", self)
        self.rotate_clockwise_action.triggered.connect(self.canvas.rotate_transform_clockwise)
        self.rotate_counterclockwise_action = QAction("Повернуть на 90° влево", self)
        self.rotate_counterclockwise_action.triggered.connect(self.canvas.rotate_transform_counterclockwise)

        transform_menu = self.menuBar().addMenu("Трансформация")
        transform_menu.addActions(
            [
                self.begin_transform_action,
                self.commit_transform_action,
                self.cancel_transform_action,
            ]
        )
        transform_menu.addSeparator()
        transform_menu.addActions(
            [
                self.flip_horizontal_action,
                self.flip_vertical_action,
                self.rotate_clockwise_action,
                self.rotate_counterclockwise_action,
            ]
        )
        self.canvas.transform_active_changed.connect(self._update_transform_actions)
        self._update_transform_actions(self.canvas.transform_active)

    def _update_transform_actions(self, active: bool) -> None:
        self.begin_transform_action.setEnabled(not active)
        for action in (
            self.commit_transform_action,
            self.cancel_transform_action,
            self.flip_horizontal_action,
            self.flip_vertical_action,
            self.rotate_clockwise_action,
            self.rotate_counterclockwise_action,
        ):
            action.setEnabled(active)

    def _install_recent_menu(self) -> None:
        file_menu = self.menuBar().actions()[0].menu()
        self.recent_menu = file_menu.addMenu("Недавние проекты")
        self.recent_menu.aboutToShow.connect(self._refresh_recent_menu)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self) -> None:
        self.recent_menu.clear()
        paths = self.session.recent.existing_paths()
        if not paths:
            action = self.recent_menu.addAction("Нет недавних проектов")
            action.setEnabled(False)
            return
        for path in paths:
            action = self.recent_menu.addAction(str(path))
            action.setData(str(path))
            action.triggered.connect(lambda checked=False, value=str(path): self.open_recent_project(value))
        self.recent_menu.addSeparator()
        self.recent_menu.addAction("Очистить список", self._clear_recent_projects)

    def _clear_recent_projects(self) -> None:
        self.session.recent.clear()
        self._save_ui_state()

    def open_recent_project(self, path: str) -> None:
        if not Path(path).exists():
            self.session.recent.remove(path)
            self._save_ui_state()
            return
        if not self._confirm_discard():
            return
        from ordpaint.core.project import ProjectError, load_project

        try:
            document = load_project(path)
        except ProjectError as exc:
            QMessageBox.critical(self, "Не удалось открыть проект", str(exc))
            self.session.recent.remove(path)
            return
        self.history.clear()
        self.history.mark_saved()
        self.current_path = path
        self.session.set_project(path)
        self.dirty = False
        self._replace_document(document)
        self._update_window_title()

    def _apply_ui_state(self, state: UIState) -> None:
        if state.geometry:
            self.restoreGeometry(state.geometry)
        if state.window_state:
            self.restoreState(state.window_state)
        self.canvas.set_zoom(state.zoom)
        self.canvas.set_show_grid(state.show_grid)
        self.canvas.set_show_rulers(state.show_rulers)
        self.canvas.set_grid_size(state.grid_size)
        self.canvas.set_brush_size(state.brush_size)
        self.canvas.set_opacity(state.opacity)
        self._set_color_from_canvas(self.canvas.color.fromString(state.color))
        self.grid_action.setChecked(self.canvas.show_grid)
        self.rulers_action.setChecked(self.canvas.show_rulers)
        self.size_spin.setValue(self.canvas.brush_size)
        self.size_slider.setValue(self.canvas.brush_size)
        self.opacity_slider.setValue(self.canvas.opacity)
        self.opacity_value.setText(f"{self.canvas.opacity}%")
        self._update_zoom_labels(round(self.canvas.zoom * 100))

    def _build_ui_state(self) -> UIState:
        return UIState(
            geometry=bytes(self.saveGeometry()),
            window_state=bytes(self.saveState()),
            zoom=self.canvas.zoom,
            show_grid=self.canvas.show_grid,
            show_rulers=self.canvas.show_rulers,
            grid_size=self.canvas.grid_size,
            brush_size=self.canvas.brush_size,
            opacity=self.canvas.opacity,
            color=self.canvas.color.name(),
            recent_paths=self.session.serialize_recent(),
        )

    def _save_ui_state(self) -> None:
        self.settings_store.save(self._build_ui_state())

    def _autosave_tick(self) -> None:
        if not self.dirty:
            return
        try:
            if self.session.tick_autosave(self.document):
                self.statusBar().showMessage("Черновик автоматически сохранён", 1500)
        except OSError:
            pass

    def _offer_recovery(self) -> None:
        recovered = self.session.recover_or_none()
        if recovered is None:
            return
        result = QMessageBox.question(
            self,
            "Восстановление проекта",
            "Найден черновик после предыдущего завершения. Восстановить его?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if result == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.current_path = None
            self.session.set_project(None)
            self.dirty = True
            self._replace_document(recovered)
            self._update_window_title()
        else:
            self.session.discard_recovery()

    def new_document(self) -> None:
        super().new_document()
        if not self.dirty and self.current_path is None:
            self.session.set_project(None)
            self.session.clear_recovery()

    def open_project(self) -> None:
        before = self.current_path
        super().open_project()
        if self.current_path and self.current_path != before:
            self.session.set_project(self.current_path)
            self._save_ui_state()

    def open_image(self) -> None:
        super().open_image()
        if self.dirty and self.current_path is None:
            self.session.set_project(None)

    def _write_project(self, path: str) -> None:
        super()._write_project(path)
        if self.current_path == path and not self.dirty:
            self.session.set_project(path)
            self.session.clear_recovery()
            self._save_ui_state()

    def closeEvent(self, event) -> None:
        if not self._confirm_discard():
            event.ignore()
            return
        try:
            if self.dirty:
                self.session.tick_autosave(self.document)
            self._save_ui_state()
        except OSError:
            pass
        event.accept()
