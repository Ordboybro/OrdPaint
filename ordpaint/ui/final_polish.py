from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QDockWidget, QToolBar, QToolButton


# The reference workspace is intentionally compact: the primary editor stays visible,
# while advanced docks remain available through View > Panels.

def _add_panel_action(window, view_menu, dock, label: str) -> None:
    action = QAction(label, window)
    action.setCheckable(True)
    action.setChecked(dock.isVisible())
    action.toggled.connect(dock.setVisible)
    dock.visibilityChanged.connect(action.setChecked)
    view_menu.addAction(action)


def install(window) -> None:
    """Apply the final presentation pass without removing advanced functionality."""
    # Keep the reference workspace clean on first launch. Advanced controls are still
    # one click away and remain restorable through the View menu.
    advanced_docks = (
        (getattr(window, "brush_presets_dock", None), "Расширенные кисти"),
        (getattr(window, "color_lab_dock", None), "Лаборатория цвета"),
    )

    view_menu = next(
        (action.menu() for action in window.menuBar().actions() if action.text() == "Вид"),
        None,
    )
    if view_menu is not None:
        view_menu.addSeparator()
        for dock, label in advanced_docks:
            if dock is None:
                continue
            _add_panel_action(window, view_menu, dock, label)
            dock.hide()

    # The main toolbar is deliberately compact and icon-first, matching the reference.
    toolbar = window.findChild(QToolBar, "mainToolbar")
    if toolbar is not None:
        toolbar.setIconSize(window.style().pixelMetric(window.style().PixelMetric.PM_SmallIconSize))
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        toolbar.setContentsMargins(6, 2, 6, 2)
        for button in toolbar.findChildren(QToolButton):
            if button.defaultAction() is None:
                continue
            action = button.defaultAction()
            if action.icon().isNull():
                # Keep controls such as zoom readable when no icon is available.
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
            else:
                button.setToolTip(action.text())
                button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)

    # Fixed dock widths prevent the canvas from being squeezed differently on
    # different screens while preserving the user's ability to resize them.
    tools_dock = getattr(window, "tools_dock", None)
    layers_dock = getattr(window, "layers_dock", None)
    color_dock = getattr(window, "color_dock", None)
    if tools_dock is not None:
        tools_dock.setMinimumWidth(205)
        tools_dock.setMaximumWidth(270)
    for dock in (layers_dock, color_dock):
        if dock is not None:
            dock.setMinimumWidth(245)
            dock.setMaximumWidth(340)

    if tools_dock is not None:
        window.resizeDocks([tools_dock], [225], Qt.Orientation.Horizontal)
    visible_right = [dock for dock in (layers_dock, color_dock) if dock is not None]
    if visible_right:
        window.resizeDocks(visible_right, [285] * len(visible_right), Qt.Orientation.Horizontal)

    window.setStyleSheet(
        window.styleSheet()
        + """
        QMainWindow { background: #17191c; }
        QToolBar#mainToolbar { min-height: 34px; max-height: 38px; }
        QToolBar#mainToolbar QToolButton { min-width: 30px; max-width: 34px; padding: 4px; }
        QToolBar#mainToolbar QToolButton:hover { background: #2d3137; }
        QToolBar#mainToolbar QToolButton:pressed { background: #3a3f47; }
        QDockWidget#toolsDock { min-width: 205px; }
        QDockWidget#layersDock, QDockWidget#colorDock { min-width: 245px; }
        QDockWidget::title { padding: 6px 9px; }
        QStatusBar { min-height: 24px; }
        """
    )
