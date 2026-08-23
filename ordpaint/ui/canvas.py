from __future__ import annotations

from collections import deque

from PySide6.QtCore import QMimeData, QPoint, QPointF, QRect, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ordpaint.core.document import Document
from ordpaint.core.tools import Tool


class Canvas(QWidget):
    """Interactive viewport, drawing surface and selection interaction layer."""

    action_started = Signal()
    zoom_changed = Signal(int)
    document_changed = Signal()
    cursor_position_changed = Signal(QPoint)
    color_picked = Signal(QColor)

    MIN_ZOOM = 0.05
    MAX_ZOOM = 16.0

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.zoom = 1.0
        self.pan = QPointF()
        self.color = QColor("#111111")
        self.brush_size = 8
        self.opacity = 100
        self.tool = Tool.BRUSH
        self._drawing = False
        self._panning = False
        self._space_pan = False
        self._last_canvas_pos: QPoint | None = None
        self._start_canvas_pos: QPoint | None = None
        self._last_pan_pos = QPointF()
        self._hover_canvas_pos: QPoint | None = None
        self.selection_rect: QRect | None = None

        self.setMouseTracking(True)
        self.setMinimumSize(500, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def set_document(self, document: Document) -> None:
        self.document = document
        self._cancel_interaction()
        self.selection_rect = None
        self.update()

    def set_tool(self, tool: Tool | str) -> None:
        self.tool = Tool(tool)
        self._cancel_interaction()
        self.update()

    def set_color(self, color: QColor) -> None:
        self.color = QColor(color)
        self.update()

    def set_brush_size(self, size: int) -> None:
        self.brush_size = max(1, min(500, int(size)))
        self.update()

    def set_opacity(self, opacity: int) -> None:
        self.opacity = max(1, min(100, int(opacity)))
        self.update()

    def set_zoom(self, zoom: float, anchor: QPointF | None = None) -> None:
        old_zoom = self.zoom
        new_zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(zoom)))
        if abs(new_zoom - old_zoom) < 1e-6:
            return
        if anchor is not None:
            before = self.widget_to_canvas(anchor)
            self.zoom = new_zoom
            if before is not None:
                top_left = self._image_top_left()
                target = QPointF(top_left.x() + before.x() * self.zoom, top_left.y() + before.y() * self.zoom)
                self.pan += anchor - target
        else:
            self.zoom = new_zoom
        self.zoom_changed.emit(round(self.zoom * 100))
        self.update()

    def zoom_in(self) -> None:
        self.set_zoom(self.zoom * 1.15, QPointF(self.rect().center()))

    def zoom_out(self) -> None:
        self.set_zoom(self.zoom / 1.15, QPointF(self.rect().center()))

    def reset_view(self) -> None:
        self.zoom = 1.0
        self.pan = QPointF()
        self.zoom_changed.emit(100)
        self.update()

    def fit_to_window(self) -> None:
        available_width = max(1, self.width() - 80)
        available_height = max(1, self.height() - 80)
        zoom = min(available_width / self.document.width, available_height / self.document.height)
        self.pan = QPointF()
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self.zoom_changed.emit(round(self.zoom * 100))
        self.update()

    def select_all(self) -> None:
        self.selection_rect = QRect(0, 0, self.document.width, self.document.height)
        self.set_tool(Tool.SELECT_RECT)
        self.update()

    def deselect(self) -> None:
        self.selection_rect = None
        self.update()

    def delete_selection(self) -> bool:
        if not self.selection_rect or self.document.active_layer.locked:
            return False
        self.action_started.emit()
        image = self.document.active_layer.pixmap.toImage()
        painter = QPainter(image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(self.selection_rect, Qt.GlobalColor.transparent)
        painter.end()
        self.document.active_layer.pixmap = QPixmap.fromImage(image)
        self.document.touch()
        self.document_changed.emit()
        self.update()
        return True

    def copy_selection(self) -> bool:
        if not self.selection_rect:
            return False
        pixmap = self.document.active_layer.pixmap.copy(self.selection_rect)
        if pixmap.isNull():
            return False
        mime = QMimeData()
        mime.setImageData(pixmap.toImage())
        QGuiApplication.clipboard().setMimeData(mime)
        return True

    def cut_selection(self) -> bool:
        if not self.copy_selection():
            return False
        return self.delete_selection()

    def paste_from_clipboard(self) -> bool:
        mime = QGuiApplication.clipboard().mimeData()
        if not mime.hasImage():
            return False
        image = mime.imageData()
        if not isinstance(image, QImage) or image.isNull():
            return False
        self.action_started.emit()
        layer = self.document.add_layer(self.document.unique_name("Pasted"))
        layer.pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(layer.pixmap)
        painter.drawImage(0, 0, image)
        painter.end()
        self.document.touch()
        self.document_changed.emit()
        self.update()
        return True

    def _image_top_left(self) -> QPointF:
        return QPointF((self.width() - self.document.width * self.zoom) / 2 + self.pan.x(), (self.height() - self.document.height * self.zoom) / 2 + self.pan.y())

    def widget_to_canvas(self, pos: QPointF) -> QPoint | None:
        top_left = self._image_top_left()
        x = int((pos.x() - top_left.x()) / self.zoom)
        y = int((pos.y() - top_left.y()) / self.zoom)
        if 0 <= x < self.document.width and 0 <= y < self.document.height:
            return QPoint(x, y)
        return None

    def canvas_to_widget(self, point: QPoint) -> QPointF:
        top_left = self._image_top_left()
        return QPointF(top_left.x() + point.x() * self.zoom, top_left.y() + point.y() * self.zoom)

    @staticmethod
    def _normalized_rect(start: QPoint, end: QPoint) -> QRect:
        return QRect(start, end).normalized()

    @property
    def _shift_pressed(self) -> bool:
        return bool(self.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier)

    @staticmethod
    def _constrained_rect(start: QPoint, end: QPoint) -> QRect:
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        side = max(abs(dx), abs(dy))
        return QRect(start, QPoint(start.x() + (side if dx >= 0 else -side), start.y() + (side if dy >= 0 else -side))).normalized()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#202124"))
        top_left = self._image_top_left()
        target = QRectF(top_left.x(), top_left.y(), self.document.width * self.zoom, self.document.height * self.zoom)
        painter.save()
        painter.setClipRect(self.rect())
        self._draw_checkerboard(painter, target)
        painter.drawPixmap(target, self.document.composite(QColor(0, 0, 0, 0)))
        painter.restore()
        painter.save()
        painter.translate(top_left)
        painter.scale(self.zoom, self.zoom)
        if self._drawing and self._start_canvas_pos and self._last_canvas_pos:
            self._draw_shape_preview(painter, self._start_canvas_pos, self._last_canvas_pos)
        if self.selection_rect:
            self._draw_selection(painter, self.selection_rect)
        painter.restore()
        if self._hover_canvas_pos and self.tool in {Tool.BRUSH, Tool.ERASER}:
            center = self.canvas_to_widget(self._hover_canvas_pos)
            radius = max(0.5, self.brush_size * self.zoom / 2)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, radius, radius)
        painter.setPen(QPen(QColor("#4a4d52"), 1))
        painter.drawRect(target)
        painter.end()

    def _draw_checkerboard(self, painter: QPainter, rect: QRectF) -> None:
        size = max(4, min(24, round(12 * self.zoom)))
        left, top, right, bottom = int(rect.left()), int(rect.top()), int(rect.right()), int(rect.bottom())
        painter.fillRect(rect, QColor("#e8e8e8"))
        for y in range(top - top % size, bottom + size, size):
            for x in range(left - left % size, right + size, size):
                if ((x // size) + (y // size)) % 2 == 0:
                    painter.fillRect(x, y, size, size, QColor("#d0d0d0"))

    def _draw_shape_preview(self, painter: QPainter, start: QPoint, end: QPoint) -> None:
        color = QColor("#63a4ff") if self.tool == Tool.SELECT_RECT else self._paint_color()
        style = Qt.PenStyle.DashLine if self.tool == Tool.SELECT_RECT else Qt.PenStyle.SolidLine
        painter.setPen(QPen(color, max(1, self.brush_size / self.zoom), style, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.tool == Tool.LINE:
            painter.drawLine(start, end)
            return
        rect = self._constrained_rect(start, end) if self._shift_pressed else self._normalized_rect(start, end)
        if self.tool in {Tool.RECTANGLE, Tool.SELECT_RECT}:
            painter.drawRect(rect)
        elif self.tool == Tool.ELLIPSE:
            painter.drawEllipse(rect)

    def _draw_selection(self, painter: QPainter, rect: QRect) -> None:
        painter.setPen(QPen(QColor("#63a4ff"), max(1, 1 / self.zoom), Qt.PenStyle.DashLine))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.SpaceModifier):
            self._panning = True
            self._space_pan = event.button() == Qt.MouseButton.LeftButton
            self._last_pan_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self.widget_to_canvas(event.position())
        if point is None:
            return
        self._hover_canvas_pos = point
        if self.tool == Tool.EYEDROPPER:
            color = self.document.composite(QColor(0, 0, 0, 0)).toImage().pixelColor(point)
            self.set_color(color)
            self.color_picked.emit(color)
            return
        if self.document.active_layer.locked:
            return
        if self.tool == Tool.SELECT_RECT:
            self._drawing = True
            self._last_canvas_pos = point
            self._start_canvas_pos = point
            return
        self.action_started.emit()
        self._drawing = True
        self._last_canvas_pos = point
        self._start_canvas_pos = point
        if self.tool == Tool.FILL:
            self._flood_fill(point)
            self._finish_action()
        elif self.tool in {Tool.BRUSH, Tool.ERASER}:
            self._draw_segment(point, point)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.position() - self._last_pan_pos
            self.pan += delta
            self._last_pan_pos = event.position()
            self.update()
            return
        point = self.widget_to_canvas(event.position())
        self._hover_canvas_pos = point
        if point is not None:
            self.cursor_position_changed.emit(point)
        if not self._drawing or point is None:
            self.update()
            return
        if self.tool in {Tool.BRUSH, Tool.ERASER} and self._last_canvas_pos is not None:
            self._draw_segment(self._last_canvas_pos, point)
        self._last_canvas_pos = point
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._panning:
            if (self._space_pan and event.button() == Qt.MouseButton.LeftButton) or (not self._space_pan and event.button() == Qt.MouseButton.MiddleButton):
                self._panning = False
                self._space_pan = False
                self.unsetCursor()
            return
        if event.button() != Qt.MouseButton.LeftButton or not self._drawing:
            return
        if self._start_canvas_pos and self._last_canvas_pos:
            if self.tool in {Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE}:
                self._draw_shape(self._start_canvas_pos, self._last_canvas_pos)
            elif self.tool == Tool.SELECT_RECT:
                self.selection_rect = self._constrained_rect(self._start_canvas_pos, self._last_canvas_pos) if self._shift_pressed else self._normalized_rect(self._start_canvas_pos, self._last_canvas_pos)
        self._finish_action(emit_changed=self.tool != Tool.SELECT_RECT)

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.set_zoom(self.zoom * factor, event.position())
            event.accept()
            return
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.pan.setX(self.pan.x() + event.angleDelta().y() / 2)
        else:
            self.pan.setY(self.pan.y() + event.angleDelta().y() / 2)
        self.update()
        event.accept()

    def leaveEvent(self, event) -> None:
        del event
        self._hover_canvas_pos = None
        self.update()

    def keyPressEvent(self, event) -> None:
        modifiers = event.modifiers()
        if event.key() == Qt.Key.Key_Escape:
            self._cancel_interaction()
        elif event.key() == Qt.Key.Key_Space:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        elif modifiers & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_A:
            self.select_all()
        elif modifiers & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_D:
            self.deselect()
        elif modifiers & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_C:
            self.copy_selection()
        elif modifiers & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_X:
            self.cut_selection()
        elif modifiers & Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_V:
            self.paste_from_clipboard()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selection()
        else:
            super().keyPressEvent(event)
            return
        event.accept()
        self.update()

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key.Key_Space and not self._panning:
            self.unsetCursor()
        super().keyReleaseEvent(event)

    def _paint_color(self) -> QColor:
        color = QColor(self.color)
        color.setAlpha(round(255 * self.opacity / 100))
        return color

    def _draw_segment(self, start: QPoint, end: QPoint) -> None:
        painter = QPainter(self.document.active_layer.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear if self.tool == Tool.ERASER else QPainter.CompositionMode.CompositionMode_SourceOver)
        color = QColor(0, 0, 0, 255) if self.tool == Tool.ERASER else self._paint_color()
        painter.setPen(QPen(color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(start, end)
        painter.end()
        self.document.touch()
        self.update()

    def _draw_shape(self, start: QPoint, end: QPoint) -> None:
        painter = QPainter(self.document.active_layer.pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(self._paint_color(), self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        rect = self._constrained_rect(start, end) if self._shift_pressed else self._normalized_rect(start, end)
        if self.tool == Tool.LINE:
            painter.drawLine(start, end)
        elif self.tool == Tool.RECTANGLE:
            painter.drawRect(rect)
        elif self.tool == Tool.ELLIPSE:
            painter.drawEllipse(rect)
        painter.end()
        self.document.touch()

    def _flood_fill(self, point: QPoint) -> None:
        image = self.document.active_layer.pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        target = image.pixelColor(point)
        replacement = self._paint_color()
        if target == replacement:
            return
        queue = deque([(point.x(), point.y())])
        visited: set[tuple[int, int]] = set()
        width, height = image.width(), image.height()
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited or not (0 <= x < width and 0 <= y < height) or image.pixelColor(x, y) != target:
                continue
            visited.add((x, y))
            image.setPixelColor(x, y, replacement)
            queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        self.document.active_layer.pixmap = QPixmap.fromImage(image)
        self.document.touch()
        self.update()

    def _cancel_interaction(self) -> None:
        self._drawing = False
        self._panning = False
        self._space_pan = False
        self._last_canvas_pos = None
        self._start_canvas_pos = None
        self.unsetCursor()

    def _finish_action(self, emit_changed: bool = True) -> None:
        self._drawing = False
        self._last_canvas_pos = None
        self._start_canvas_pos = None
        if emit_changed:
            self.document_changed.emit()
        self.update()
