"""PySide6 compatibility hooks for the desktop/test runtime."""

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu


def _find_menu(window, title: str):
    for menu in window.menuBar().findChildren(QMenu):
        if menu.title() == title:
            return menu
    return None


def _install_recent_menu(self) -> None:
    file_menu = _find_menu(self, "Файл")
    if file_menu is None:
        return
    self.recent_menu = file_menu.addMenu("Недавние проекты")
    self.recent_menu.aboutToShow.connect(self._refresh_recent_menu)
    self._refresh_recent_menu()


def _install_image_resize_actions(self) -> None:
    self.resize_canvas_action = QAction("Размер холста…", self, shortcut="Ctrl+Alt+C")
    self.resize_canvas_action.triggered.connect(self.resize_canvas)
    self.scale_image_action = QAction("Размер изображения…", self, shortcut="Ctrl+Alt+I")
    self.scale_image_action.triggered.connect(self.scale_image)
    image_menu = _find_menu(self, "Изображение")
    if image_menu is None:
        return
    image_menu.addSeparator()
    image_menu.addActions([self.resize_canvas_action, self.scale_image_action])


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
    edit_menu = _find_menu(self, "Правка")
    if edit_menu is None:
        return
    menu = edit_menu.addMenu("Трансформация")
    menu.addActions([self.begin_transform_action, self.commit_transform_action, self.cancel_transform_action])
    menu.addSeparator()
    menu.addActions(
        [
            self.flip_horizontal_action,
            self.flip_vertical_action,
            self.rotate_clockwise_action,
            self.rotate_counterclockwise_action,
        ]
    )
    self.transform_menu = menu
    self.canvas.transform_active_changed.connect(self._update_transform_actions)
    self._update_transform_actions(self.canvas.transform_active)


def _install() -> None:
    try:
        from ordpaint.ui import application_window
    except Exception:
        return
    application_window.MainWindow._install_recent_menu = _install_recent_menu
    application_window.MainWindow._install_image_resize_actions = _install_image_resize_actions
    application_window.MainWindow._install_transform_actions = _install_transform_actions


_install()
