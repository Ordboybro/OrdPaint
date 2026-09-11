import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu


@pytest.fixture(scope="session")
def qt_app():
    app = QApplication.instance()
    return app or QApplication([])


@pytest.fixture(scope="session")
def qapp(qt_app):
    """Compatibility alias for tests that use the conventional qapp fixture name."""
    return qt_app


@pytest.fixture(autouse=True)
def ensure_qt_app(qt_app):
    """Keep QPixmap/QPainter tests safe even when they omit an explicit fixture."""
    return qt_app


@pytest.fixture(autouse=True)
def patch_application_window_menu_installation(monkeypatch: pytest.MonkeyPatch):
    from ordpaint.ui import application_window

    def find_menu(window, title: str):
        return next((menu for menu in window.menuBar().findChildren(QMenu) if menu.title() == title), None)

    def install_image_resize_actions(self) -> None:
        self.resize_canvas_action = QAction("Размер холста…", self, shortcut="Ctrl+Alt+C")
        self.resize_canvas_action.triggered.connect(self.resize_canvas)
        self.scale_image_action = QAction("Размер изображения…", self, shortcut="Ctrl+Alt+I")
        self.scale_image_action.triggered.connect(self.scale_image)
        image_menu = find_menu(self, "Изображение")
        if image_menu is not None:
            image_menu.addSeparator()
            image_menu.addActions([self.resize_canvas_action, self.scale_image_action])

    def install_transform_actions(self) -> None:
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
        edit_menu = find_menu(self, "Правка")
        if edit_menu is None:
            return
        menu = edit_menu.addMenu("Трансформация")
        menu.addActions([self.begin_transform_action, self.commit_transform_action, self.cancel_transform_action])
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

    monkeypatch.setattr(application_window.MainWindow, "_install_image_resize_actions", install_image_resize_actions)
    monkeypatch.setattr(application_window.MainWindow, "_install_transform_actions", install_transform_actions)
