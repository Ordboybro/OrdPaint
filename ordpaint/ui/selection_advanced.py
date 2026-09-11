from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QAction, QActionGroup

from ordpaint.core.selection import SelectionMode
from ordpaint.core.tools import Tool
from ordpaint.ui.canvas import Canvas


def install(window) -> None:
    """Install advanced selection modes while keeping the reference top-level menu layout."""
    if getattr(window, "_ordpaint_selection_advanced", False):
        return
    window.canvas.selection.set_document_size(window.document.width, window.document.height)
    actions = {}

    parent_menu = next((action.menu() for action in window.menuBar().actions() if action.text() == "Правка"), None)
    if parent_menu is None:
        parent_menu = next((action.menu() for action in window.menuBar().actions() if action.text() == "Изображение"), None)
    if parent_menu is None:
        return
    menu = parent_menu.addMenu("Выделение")

    tools = (
        ("rect", "Прямоугольник", "M", Tool.SELECT_RECT),
        ("ellipse", "Эллипс", "Shift+M", Tool.SELECT_ELLIPSE),
        ("polygon", "Многоугольник", "P", Tool.SELECT_POLYGON),
        ("lasso", "Лассо", "Shift+P", Tool.SELECT_LASSO),
        ("crop", "Кадрирование", "C", Tool.CROP),
    )
    tool_group = QActionGroup(window)
    tool_group.setExclusive(True)
    for key, text, shortcut, tool in tools:
        if tool is Tool.SELECT_RECT:
            action = window.tool_actions[Tool.SELECT_RECT]
            action.setCheckable(True)
        else:
            action = QAction(text, window)
            action.setShortcut(shortcut)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, value=tool: window.canvas.set_tool(value))
        menu.addAction(action)
        tool_group.addAction(action)
        actions[key] = action
    actions["rect"].setChecked(window.canvas.tool is Tool.SELECT_RECT)

    mode_menu = menu.addMenu("Режим")
    mode_group = QActionGroup(window)
    mode_group.setExclusive(True)
    for mode, text, shortcut in (
        (SelectionMode.REPLACE, "Заменить", "Alt+1"),
        (SelectionMode.ADD, "Добавить", "Alt+2"),
        (SelectionMode.SUBTRACT, "Вычесть", "Alt+3"),
        (SelectionMode.INTERSECT, "Пересечь", "Alt+4"),
    ):
        action = QAction(text, window)
        action.setShortcut(shortcut)
        action.setCheckable(True)
        action.triggered.connect(lambda checked=False, value=mode: window.canvas.set_selection_mode(value))
        mode_menu.addAction(action)
        mode_group.addAction(action)
        if mode is SelectionMode.REPLACE:
            action.setChecked(True)

    window.tool_actions.update(
        {
            Tool.SELECT_ELLIPSE: actions["ellipse"],
            Tool.SELECT_POLYGON: actions["polygon"],
            Tool.SELECT_LASSO: actions["lasso"],
            Tool.CROP: actions["crop"],
        }
    )

    original_press = Canvas.mousePressEvent
    original_move = Canvas.mouseMoveEvent
    original_release = Canvas.mouseReleaseEvent
    original_set_document = Canvas.set_document

    def set_document(self, document):
        original_set_document(self, document)
        self.selection.set_document_size(document.width, document.height)

    def press(self, event):
        if self.tool in {Tool.SELECT_ELLIPSE, Tool.SELECT_POLYGON, Tool.SELECT_LASSO}:
            point = self.widget_to_canvas(event.position())
            if point is None or event.button() != Qt.MouseButton.LeftButton:
                return
            self._advanced_selection_points = [QPoint(point)]
            self._advanced_selection_start = QPoint(point)
            self._advanced_selection_current = QPoint(point)
            self._advanced_selection_dragging = True
            event.accept()
            self.update()
            return
        if self.tool is Tool.CROP:
            point = self.widget_to_canvas(event.position())
            if point is not None and event.button() == Qt.MouseButton.LeftButton:
                self._crop_start = QPoint(point)
                self._crop_current = QPoint(point)
                self._crop_dragging = True
                event.accept()
                self.update()
                return
        original_press(self, event)

    def move(self, event):
        if getattr(self, "_advanced_selection_dragging", False):
            point = self.widget_to_canvas(event.position())
            if point is not None:
                if self.tool is Tool.SELECT_LASSO:
                    points = getattr(self, "_advanced_selection_points", [])
                    if not points or (point - points[-1]).manhattanLength() >= 2:
                        points.append(QPoint(point))
                else:
                    self._advanced_selection_current = QPoint(point)
            self.update()
            event.accept()
            return
        if getattr(self, "_crop_dragging", False):
            point = self.widget_to_canvas(event.position())
            if point is not None:
                self._crop_current = QPoint(point)
            self.update()
            event.accept()
            return
        original_move(self, event)

    def release(self, event):
        if getattr(self, "_advanced_selection_dragging", False):
            self._advanced_selection_dragging = False
            point = self.widget_to_canvas(event.position()) or getattr(self, "_advanced_selection_current", self._advanced_selection_start)
            mode = getattr(self, "_selection_mode", SelectionMode.REPLACE)
            if self.tool is Tool.SELECT_ELLIPSE:
                self.selection.set_ellipse(QRect(self._advanced_selection_start, point).normalized(), mode)
            elif self.tool is Tool.SELECT_LASSO:
                points = getattr(self, "_advanced_selection_points", [])
                if len(points) >= 3:
                    self.selection.set_lasso(points, mode)
            else:
                start = self._advanced_selection_start
                end = point
                self.selection.set_polygon([start, QPoint(end.x(), start.y()), end, QPoint(start.x(), end.y())], mode)
            self.document_changed.emit()
            self.update()
            event.accept()
            return
        if getattr(self, "_crop_dragging", False):
            self._crop_dragging = False
            point = self.widget_to_canvas(event.position()) or self._crop_current
            self.selection.set_rect(QRect(self._crop_start, point).normalized(), SelectionMode.REPLACE)
            self.update()
            event.accept()
            return
        original_release(self, event)

    Canvas.mousePressEvent = press
    Canvas.mouseMoveEvent = move
    Canvas.mouseReleaseEvent = release
    Canvas.set_document = set_document
    Canvas._ordpaint_selection_advanced = True
    window._ordpaint_selection_advanced = True
    window.selection_actions = actions
