from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QAction

from ordpaint.ui.canvas import Canvas


def install(window) -> None:
    """Add optional snap-to-grid without changing the document model."""
    if not getattr(Canvas, "_ordpaint_snap_support", False):
        original_init = Canvas.__init__
        original_widget_to_canvas = Canvas.widget_to_canvas

        def init(self, *args, **kwargs) -> None:
            original_init(self, *args, **kwargs)
            self.snap_to_grid = False

        def widget_to_canvas(self, pos):
            point = original_widget_to_canvas(self, pos)
            if point is None or not getattr(self, "snap_to_grid", False):
                return point
            size = max(2, int(self.grid_size))
            x = min(self.document.width - 1, max(0, round(point.x() / size) * size))
            y = min(self.document.height - 1, max(0, round(point.y() / size) * size))
            return QPoint(x, y)

        Canvas.__init__ = init
        Canvas.widget_to_canvas = widget_to_canvas
        Canvas._ordpaint_snap_support = True

    action = QAction("Привязка к сетке", window, checkable=True, shortcut="Ctrl+Shift+G")
    action.setToolTip("Привязывать курсор рисования и выделения к узлам сетки")
    action.toggled.connect(lambda checked: setattr(window.canvas, "snap_to_grid", bool(checked)))
    view_menu = next((item.menu() for item in window.menuBar().actions() if item.text() == "Вид"), None)
    if view_menu is not None:
        view_menu.addAction(action)
    window.snap_grid_action = action
