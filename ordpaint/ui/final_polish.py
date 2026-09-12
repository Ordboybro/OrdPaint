from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QStyle, QTabBar, QToolBar, QToolButton, QSizePolicy

from ordpaint.ui.color_lab import ColorWheel

_REFERENCE_BG = "#171b20"
_ACCENT = "#ff7a00"


def _menu(window, title: str):
    for menu in window.menuBar().findChildren(QMenu):
        if menu.title() == title:
            return menu
    return None


def _style(window) -> None:
    window.setStyleSheet(f"""
        QMainWindow {{ background: {_REFERENCE_BG}; }}
        QMenuBar {{
            background: #1b2026; color: #d8dde3; border-bottom: 1px solid #2b323b;
            padding: 1px 6px; spacing: 4px;
        }}
        QMenuBar::item {{ padding: 6px 9px; border-radius: 4px; }}
        QMenuBar::item:selected {{ background: #2b323b; color: #ffffff; }}
        QMenu {{
            background: #20262d; color: #d8dde3; border: 1px solid #343c46;
            padding: 5px;
        }}
        QMenu::item {{ padding: 6px 24px 6px 10px; border-radius: 4px; }}
        QMenu::item:selected {{ background: #343c46; color: #ffffff; }}
        QMenu::separator {{ height: 1px; background: #343c46; margin: 5px 6px; }}
        QToolBar {{
            background: #1b2026; border: 0; border-bottom: 1px solid #2b323b;
            spacing: 6px; padding: 4px 8px;
        }}
        QToolButton {{
            color: #d8dde3; background: transparent; border: 1px solid transparent;
            border-radius: 5px; padding: 3px 6px; min-width: 62px; min-height: 48px;
        }}
        QToolButton:hover {{ background: #282f37; border-color: #3a434d; }}
        QToolButton:pressed {{ background: #333b45; border-color: {_ACCENT}; }}
        QDockWidget {{ color: #e1e5ea; font-weight: 600; }}
        QDockWidget::title {{
            background: #1b2026; border: 1px solid #2d353e; border-bottom: 0;
            padding: 7px 9px; text-align: left;
        }}
        QTabBar::tab {{
            background: #1b2026; color: #aeb6bf; padding: 7px 11px;
            border: 1px solid #2d353e; border-bottom: 0; border-radius: 5px 5px 0 0;
        }}
        QTabBar::tab:selected {{ background: #252c34; color: #ffffff; border-top: 2px solid {_ACCENT}; }}
        QStatusBar {{ background: #1b2026; color: #aeb6bf; border-top: 1px solid #2b323b; }}
        QStatusBar::item {{ border: 0; padding: 0 7px; }}
        QToolTip {{ background: #20262d; color: #ffffff; border: 1px solid #46515c; padding: 5px; }}
    """)


def _install_document_bar(window) -> None:
    bar = getattr(window, "_ordpaint_document_toolbar", None)
    if bar is None:
        bar = QToolBar(window)
        bar.setObjectName("documentToolbar")
        bar.setMovable(False)
        bar.setFloatable(False)
        bar.setIconSize(QSize(16, 16))
        bar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        bar.setStyleSheet("QToolBar { background: #171b20; border: 0; padding: 0 8px; }")
        window.addToolBar(Qt.ToolBarArea.TopToolBarArea, bar)
        window._ordpaint_document_toolbar = bar

    tabs = getattr(window, "_ordpaint_document_tabs", None)
    if tabs is None:
        tabs = QTabBar(bar)
        tabs.setObjectName("documentTabs")
        tabs.setExpanding(False)
        tabs.setMovable(True)
        tabs.setUsesScrollButtons(True)
        tabs.setDocumentMode(True)
        tabs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        bar.addWidget(tabs)
        window._ordpaint_document_tabs = tabs

    plus = getattr(window, "_ordpaint_new_tab_action", None)
    if plus is None:
        plus = QAction("+", window)
        plus.setToolTip("Новый документ")
        plus.triggered.connect(lambda: window._new_document())
        bar.addAction(plus)
        window._ordpaint_new_tab_action = plus

    fit = getattr(window, "_ordpaint_fit_action", None)
    if fit is None:
        fit = QAction(window.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon), "", window)
        fit.setToolTip("Вписать изображение в окно")
        fit.triggered.connect(window.canvas.fit_to_window)
        bar.addAction(fit)
        window._ordpaint_fit_action = fit

    reset = getattr(window, "_ordpaint_reset_action", None)
    if reset is None:
        reset = QAction("100%", window)
        reset.setToolTip("Сбросить масштаб до 100%")
        reset.triggered.connect(window.canvas.reset_view)
        bar.insertAction(fit, reset)
        window._ordpaint_reset_action = reset


def _install_reference_docks(window) -> None:
    tools = getattr(window, "tools_dock", None)
    layers = getattr(window, "layers_dock", None)
    colors = getattr(window, "color_dock", None)
    if tools is not None:
        tools.setWindowTitle("Инструменты")
        tools.setMinimumWidth(150)
        tools.setMaximumWidth(210)
    if layers is not None:
        layers.setWindowTitle("Слои")
        layers.setMinimumWidth(220)
        layers.setMaximumWidth(285)
    if colors is not None:
        colors.setWindowTitle("Цвета")
        colors.setMinimumWidth(220)
        colors.setMaximumWidth(285)
        wheel = colors.findChild(ColorWheel)
        if wheel is not None:
            wheel.setObjectName("referenceWheel")
            wheel.setFixedSize(178, 178)
            if not getattr(wheel, "_reference_connected", False):
                wheel.colorSelected.connect(window.canvas.set_color)
                wheel._reference_connected = True


def _install_top_toolbar(window) -> None:
    toolbar = getattr(window, "toolbar", None) or getattr(window, "main_toolbar", None)
    if toolbar is None:
        return
    toolbar.setObjectName("mainToolbar")
    toolbar.setMovable(False)
    toolbar.setFloatable(False)
    toolbar.setIconSize(QSize(21, 21))
    toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    toolbar.setContentsMargins(8, 3, 8, 3)
    labels = {
        getattr(window, "new_action", None): "Создать",
        getattr(window, "open_action", None): "Открыть",
        getattr(window, "save_action", None): "Сохранить",
        getattr(window, "export_action", None): "Экспорт",
        getattr(window, "undo_action", None): "Отменить",
        getattr(window, "redo_action", None): "Повторить",
    }
    for action, label in labels.items():
        if action is not None:
            action.setText(label)
            action.setIconVisibleInMenu(True)
    toolbar.setMinimumHeight(56)
    toolbar.setMaximumHeight(64)
    for button in toolbar.findChildren(QToolButton):
        button.setMinimumSize(66, 52)
        button.setMaximumSize(88, 58)


def _install_menu_structure(window) -> None:
    bar = window.menuBar()
    desired = ["Файл", "Правка", "Вид", "Изображение", "Слой", "Справка"]
    menus = {menu.title(): menu for menu in bar.findChildren(QMenu)}
    for title in desired:
        menus.setdefault(title, bar.addMenu(title))
    tools_menu = menus.get("Инструменты")
    if tools_menu is not None:
        bar.removeAction(tools_menu.menuAction())
    transform_menu = menus.get("Трансформация")
    image_menu = menus.get("Изображение")
    if transform_menu is not None and image_menu is not None:
        for action in list(transform_menu.actions()):
            if action not in image_menu.actions():
                image_menu.addAction(action)
        bar.removeAction(transform_menu.menuAction())
    view = menus.get("Вид")
    if view is not None and view.findChild(QMenu, "panelsMenu") is None:
        panels = view.addMenu("Панели")
        panels.setObjectName("panelsMenu")
        for dock, title in (
            (getattr(window, "tools_dock", None), "Инструменты"),
            (getattr(window, "layers_dock", None), "Слои"),
            (getattr(window, "color_dock", None), "Цвета"),
        ):
            if dock is not None:
                action = panels.addAction(title)
                action.setCheckable(True)
                action.setChecked(dock.isVisible())
                action.toggled.connect(dock.setVisible)
    for title in reversed(desired):
        action = next((a for a in bar.actions() if a.text() == title), None)
        if action is not None:
            bar.removeAction(action)
            bar.insertAction(bar.actions()[0] if bar.actions() else None, action)


def install(window) -> None:
    """Final reference pass: compact default workspace with advanced panels retained."""
    _style(window)
    _install_menu_structure(window)
    _install_top_toolbar(window)
    _install_document_bar(window)
    _install_reference_docks(window)

    try:
        if window.canvas.document.width != 1200 or window.canvas.document.height != 800:
            window._replace_document(window.canvas.document.__class__(1200, 800))
    except (AttributeError, TypeError):
        pass

    try:
        window.statusBar().showMessage("1200 × 800 px")
    except AttributeError:
        pass

    for dock in (
        getattr(window, "brush_presets_dock", None),
        getattr(window, "color_lab_dock", None),
        getattr(window, "layer_group_dock", None),
    ):
        if dock is not None:
            dock.hide()

    window.setMinimumSize(900, 600)
    window.resize(1120, 720)
