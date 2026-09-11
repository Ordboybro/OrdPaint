import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu

from ordpaint.ui.application_window import MainWindow as BaseMainWindow
from ordpaint.ui.brush_presets import BrushPresetDock
from ordpaint.ui.color_lab import ColorLabDock
from ordpaint.ui.crash_reporter import install as install_crash_reporter
from ordpaint.ui.final_polish import install as install_final_polish
from ordpaint.ui.grid_enhancement import install as install_grid_enhancement
from ordpaint.ui.grid_ux import install as install_grid_ux
from ordpaint.ui.image_ops import install as install_image_ops
from ordpaint.ui.keyboard_polish import install as install_keyboard_polish
from ordpaint.ui.layer_groups import LayerGroupDock
from ordpaint.ui.layout_restore import install as install_layout_restore
from ordpaint.ui.polish import install as install_polish
from ordpaint.ui.pressure_input import install as install_pressure_input
from ordpaint.ui.recovery_polish import install as install_recovery_polish
from ordpaint.ui.resize_integration import install as install_resize
from ordpaint.ui.selection_advanced import install as install_selection_advanced
from ordpaint.ui.selection_clip import install as install_selection_clip
from ordpaint.ui.stability import install as install_stability
from ordpaint.ui.transform_advanced import install as install_transform_advanced
from ordpaint.ui.transform_integration import install as install_transform


class MainWindow(BaseMainWindow):
    """Release entry point with stable access to the existing menus."""

    def _find_menu(self, title: str) -> QMenu | None:
        return next((menu for menu in self.menuBar().findChildren(QMenu) if menu.title() == title), None)

    def _install_transform_actions(self) -> None:
        self.begin_transform_action = QAction("Свободное трансформирование", self, shortcut="Ctrl+T")
        self.begin_transform_action.triggered.connect(self._begin_transform)
        self.commit_transform_action = QAction("Применить трансформацию", self, shortcut="Return")
        self.commit_transform_action.triggered.connect(self._commit_transform)
        self.cancel_transform_action = QAction("Отменить трансформацию", self, shortcut="Escape")
        self.cancel_transform_action.triggered.connect(self._cancel_transform)
        self.flip_horizontal_action = QAction("Отразить по горизонтали", self)
        self.flip_horizontal_action.triggered.connect(self._flip_transform_horizontal)
        self.flip_vertical_action = QAction("Отразить по вертикали", self)
        self.flip_vertical_action.triggered.connect(self._flip_transform_vertical)
        self.rotate_clockwise_action = QAction("Повернуть на 90° вправо", self)
        self.rotate_clockwise_action.triggered.connect(self._rotate_transform_clockwise)
        self.rotate_counterclockwise_action = QAction("Повернуть на 90° влево", self)
        self.rotate_counterclockwise_action.triggered.connect(self._rotate_transform_counterclockwise)

        edit_menu = self._find_menu("Правка")
        if edit_menu is not None:
            menu = edit_menu.addMenu("Трансформация")
            menu.addActions([
                self.begin_transform_action,
                self.commit_transform_action,
                self.cancel_transform_action,
            ])
            menu.addSeparator()
            menu.addActions([
                self.flip_horizontal_action,
                self.flip_vertical_action,
                self.rotate_clockwise_action,
                self.rotate_counterclockwise_action,
            ])
            self.transform_menu = menu

        self.canvas.transform_active_changed.connect(self._update_transform_actions)
        self._update_transform_actions(self.canvas.transform_active)

    def _install_image_resize_actions(self) -> None:
        self.resize_canvas_action = QAction("Размер холста…", self, shortcut="Ctrl+Alt+C")
        self.resize_canvas_action.triggered.connect(self.resize_canvas)
        self.scale_image_action = QAction("Размер изображения…", self, shortcut="Ctrl+Alt+I")
        self.scale_image_action.triggered.connect(self.scale_image)
        image_menu = self._find_menu("Изображение")
        if image_menu is not None:
            image_menu.addSeparator()
            image_menu.addActions([self.resize_canvas_action, self.scale_image_action])


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrdPaint")
    app.setApplicationDisplayName("OrdPaint")
    app.setOrganizationName("OrdStudio")
    app.setOrganizationDomain("ordpaint.local")
    app.setStyle("Fusion")
    install_crash_reporter()
    install_grid_enhancement()
    install_stability()

    window = MainWindow()
    install_grid_ux(window)
    install_polish(window)
    install_pressure_input()
    install_resize(window)
    install_transform(window)
    install_transform_advanced(window)
    install_selection_advanced(window)
    install_selection_clip()
    install_image_ops(window)
    install_keyboard_polish(window)
    install_recovery_polish(window)

    window.brush_presets_dock = BrushPresetDock(window)
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, window.brush_presets_dock)
    window.color_lab_dock = ColorLabDock(window)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.color_lab_dock)
    window.layer_group_dock = LayerGroupDock(window)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.layer_group_dock)

    install_layout_restore(window)
    install_final_polish(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
