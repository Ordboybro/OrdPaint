from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMessageBox, QStyle, QTabBar, QToolBar, QToolButton, QSizePolicy, QWidget

from ordpaint.ui.color_lab import ColorWheel


_REFERENCE_BG = "#171b20"
_ACCENT = "#ff7a00"


def _menu(window, title: str):
    for menu in window.menuBar().findChildren(QMenu):
        if menu.title() == title:
            return menu
    return None


def _add_panel_action(view_menu, dock, label: str, *, default_hidden: bool) -> None:
    action = QAction(label, view_menu)
    action.setCheckable(True)
    action.setChecked(dock.isVisible())
    action.toggled.connect(dock.setVisible)
    dock.visibilityChanged.connect(action.setChecked)
    view_menu.addAction(action)
    if default_hidden:
        dock.hide()


def _install_reference_menus(window) -> None:
    view_menu = _menu(window, "Вид")
    image_menu = _menu(window, "Изображение")
    if view_menu is None:
        return

    tools_menu = _menu(window, "Инструменты")
    if tools_menu is not None:
        window.menuBar().removeAction(tools_menu.menuAction())

    transform_menu = _menu(window, "Трансформация")
    if transform_menu is not None:
        if image_menu is not None:
            image_menu.addSeparator()
            for action in transform_menu.actions():
                image_menu.addAction(action)
        window.menuBar().removeAction(transform_menu.menuAction())

    panels = QMenu("Панели", view_menu)
    view_menu.addSeparator()
    view_menu.addMenu(panels)

    advanced_docks = (
        (getattr(window, "brush_presets_dock", None), "Расширенные кисти"),
        (getattr(window, "color_lab_dock", None), "Лаборатория цвета"),
        (getattr(window, "layer_group_dock", None), "Группы слоёв"),
        (window.findChild(type(window.tools_dock), "brushSettingsDock"), "Доп. параметры кисти"),
        (window.findChild(type(window.tools_dock), "colorStudioDock"), "Расширенная панель цвета"),
    )
    saved_layout = bool(getattr(getattr(window, "ui_state", None), "window_state", b""))
    for dock, label in advanced_docks:
        if dock is None:
            continue
        _add_panel_action(panels, dock, label, default_hidden=not saved_layout)

    if not any(action.text() == "Справка" for action in window.menuBar().actions()):
        help_menu = window.menuBar().addMenu("Справка")
        shortcuts = QAction("Горячие клавиши", window)

        def show_shortcuts() -> None:
            QMessageBox.information(
                window,
                "Горячие клавиши",
                "Ctrl+N — новый документ\n"
                "Ctrl+O — открыть\n"
                "Ctrl+S — сохранить\n"
                "Ctrl+Z / Ctrl+Y — отменить / повторить\n"
                "B / E — кисть / ластик\n"
                "G — заливка\n"
                "I — пипетка\n"
                "M — выделение\n"
                "Ctrl+0 — 100%\n"
                "Ctrl+Shift+0 — вписать в окно",
            )

        shortcuts.triggered.connect(show_shortcuts)
        about = QAction("О программе OrdPaint", window)
        about.triggered.connect(
            lambda: QMessageBox.about(
                window,
                "OrdPaint",
                "OrdPaint — растровый редактор для рисования, работы со слоями и безопасного сохранения проектов.",
            )
        )
        help_menu.addActions([shortcuts, about])


def _install_document_strip(window) -> None:
    toolbar = window.findChild(QToolBar, "mainToolbar")
    if toolbar is None or window.findChild(QToolBar, "documentToolbar") is not None:
        return

    for action in (window.fit_view_action, window.reset_view_action):
        if action in toolbar.actions():
            toolbar.removeAction(action)
    zoom_label_action = None
    for action in toolbar.actions():
        if toolbar.widgetForAction(action) is window.zoom_label:
            zoom_label_action = action
            break
    if zoom_label_action is not None:
        toolbar.removeAction(zoom_label_action)

    document_toolbar = QToolBar("Документ", window)
    document_toolbar.setObjectName("documentToolbar")
    document_toolbar.setMovable(False)
    document_toolbar.setFloatable(False)
    document_toolbar.setContentsMargins(8, 2, 8, 2)

    tabs = QTabBar(document_toolbar)
    tabs.setObjectName("documentTabs")
    tabs.setDocumentMode(True)
    tabs.setExpanding(False)
    tabs.setMovable(False)
    tabs.setTabsClosable(False)
    tabs.setShape(QTabBar.Shape.RoundedNorth)
    tabs.addTab("Безымянный*")
    tabs.setCurrentIndex(0)
    document_toolbar.addWidget(tabs)

    new_button = QToolButton(document_toolbar)
    new_button.setAutoRaise(True)
    new_button.setText("+")
    new_button.setToolTip("Новый документ")
    new_button.clicked.connect(window.new_document)
    document_toolbar.addWidget(new_button)

    document_toolbar.addSeparator()
    spacer = QWidget(document_toolbar)
    spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
    document_toolbar.addWidget(spacer)
    zoom_button = QToolButton(document_toolbar)
    zoom_button.setDefaultAction(window.fit_view_action)
    zoom_button.setToolTip("Вписать в окно")
    document_toolbar.addWidget(zoom_button)
    reset_button = QToolButton(document_toolbar)
    reset_button.setDefaultAction(window.reset_view_action)
    reset_button.setToolTip("100%")
    document_toolbar.addWidget(reset_button)

    window.addToolBar(Qt.ToolBarArea.TopToolBarArea, document_toolbar)
    window._ordpaint_document_tabs = tabs

    original_update_title = window._update_window_title

    def update_title() -> None:
        original_update_title()
        path = getattr(window, "current_path", None)
        name = Path(path).name if path else "Безымянный"
        dirty = "*" if getattr(window, "dirty", False) else ""
        tabs.setTabText(0, f"{name}{dirty}")

    window._update_window_title = update_title
    update_title()


def _install_toolbar_icons(window) -> None:
    toolbar = window.findChild(QToolBar, "mainToolbar")
    if toolbar is None:
        return
    style = window.style()
    standard = {
        "Новый": QStyle.StandardPixmap.SP_FileIcon,
        "Открыть…": QStyle.StandardPixmap.SP_DialogOpenButton,
        "Сохранить": QStyle.StandardPixmap.SP_DialogSaveButton,
        "Экспортировать изображение…": QStyle.StandardPixmap.SP_ArrowRight,
        "Отменить": QStyle.StandardPixmap.SP_ArrowBack,
        "Повторить": QStyle.StandardPixmap.SP_ArrowForward,
    }
    for button in toolbar.findChildren(QToolButton):
        action = button.defaultAction()
        if action is None:
            continue
        if action.icon().isNull() and action.text() in standard:
            button.setIcon(style.standardIcon(standard[action.text()]))
        if not button.toolTip():
            button.setToolTip(action.text())


def _install_toolbar_style(window) -> None:
    toolbar = window.findChild(QToolBar, "mainToolbar")
    if toolbar is None:
        return
    icon_size = max(18, window.style().pixelMetric(QStyle.PixelMetric.PM_SmallIconSize))
    toolbar.setIconSize(QSize(icon_size, icon_size))
    toolbar.setContentsMargins(8, 0, 8, 0)
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    for button in toolbar.findChildren(QToolButton):
        if button.defaultAction() is None:
            continue
        action = button.defaultAction()
        if not action.icon().isNull():
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            button.setToolTip(action.text())
            button.setMinimumSize(60, 50)
            button.setMaximumSize(82, 56)
        else:
            button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)


def _install_reference_color_wheel(window) -> None:
    dock = getattr(window, "color_dock", None)
    if dock is None or getattr(dock, "_reference_wheel", None) is not None:
        return
    panel = dock.widget()
    layout = panel.layout() if panel is not None else None
    if layout is None:
        return
    wheel = ColorWheel(panel)
    wheel.setObjectName("referenceWheel")
    wheel.setFixedSize(178, 178)
    wheel.colorSelected.connect(window.canvas.set_color)
    layout.insertWidget(1, wheel, 0, Qt.AlignmentFlag.AlignHCenter)
    dock._reference_wheel = wheel


def _install_reference_panel_details(window) -> None:
    tools = getattr(window, "tools_dock", None)
    if tools is not None:
        tools.setWindowTitle("Инструменты")
    layers = getattr(window, "layers_dock", None)
    if layers is not None:
        layers.setWindowTitle("Слои")
    colors = getattr(window, "color_dock", None)
    if colors is not None:
        colors.setWindowTitle("Цвета")
        colors.setMinimumWidth(220)
        colors.setMaximumWidth(285)
    label = getattr(window, "layer_status_label", None)
    if label is not None:
        label.hide()


def _install_workspace_geometry(window) -> None:
    state = getattr(window, "ui_state", None)
    if not getattr(state, "geometry", b""):
        window.resize(1200, 800)

    tools_dock = getattr(window, "tools_dock", None)
    layers_dock = getattr(window, "layers_dock", None)
    color_dock = getattr(window, "color_dock", None)
    if tools_dock is not None:
        tools_dock.setMinimumWidth(185)
        tools_dock.setMaximumWidth(220)
    for dock in (layers_dock, color_dock):
        if dock is not None:
            dock.setMinimumWidth(220)
            dock.setMaximumWidth(285)

    if tools_dock is not None:
        window.resizeDocks([tools_dock], [195], Qt.Orientation.Horizontal)
    right = [dock for dock in (layers_dock, color_dock) if dock is not None]
    if right:
        window.resizeDocks(right, [255] * len(right), Qt.Orientation.Horizontal)


def install(window) -> None:
    _install_reference_menus(window)
    _install_document_strip(window)
    _install_toolbar_icons(window)
    _install_toolbar_style(window)
    _install_reference_color_wheel(window)
    _install_reference_panel_details(window)
    _install_workspace_geometry(window)

    window.setStyleSheet(
        window.styleSheet()
        + f"""
        QMainWindow {{ background: {_REFERENCE_BG}; }}
        QMenuBar {{ min-height: 30px; padding-left: 8px; }}
        QMenuBar::item {{ padding: 7px 12px; }}
        QToolBar#mainToolbar {{ min-height: 56px; max-height: 60px; spacing: 3px; }}
        QToolBar#mainToolbar QToolButton {{ padding: 3px 6px; border-radius: 5px; }}
        QToolBar#mainToolbar QToolButton:hover {{ background: #2b3037; }}
        QToolBar#mainToolbar QToolButton:pressed {{ background: #3a4048; }}
        QToolBar#documentToolbar {{ min-height: 42px; max-height: 46px; background: #15191e; border-bottom: 1px solid #30353c; }}
        QTabBar#documentTabs::tab {{ min-width: 150px; padding: 7px 14px; margin-right: 2px; color: #d7dbe0; background: #20252b; border: 1px solid #30363e; border-bottom: none; }}
        QTabBar#documentTabs::tab:selected {{ color: #ffffff; background: #2a3037; border-top: 2px solid {_ACCENT}; }}
        QTabBar#documentTabs::tab:hover {{ background: #282e35; }}
        QToolBar#documentToolbar QToolButton {{ min-width: 30px; max-width: 38px; font-size: 18px; }}
        QDockWidget#toolsDock {{ min-width: 185px; }}
        QDockWidget#layersDock, QDockWidget#colorDock {{ min-width: 220px; }}
        QDockWidget::title {{ padding: 6px 9px; background: #1d2228; }}
        QStatusBar {{ min-height: 24px; }}
        #referenceWheel {{ margin: 2px; }}
        """
    )
