from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPoint, QPointF, QRect, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ordpaint.core.document import Document
from ordpaint.core.tools import Tool


class Canvas(QWidget):
    action_started = Signal()
    zoom_changed = Signal(int)
    document_changed = Signal()
    cursor_position_changed = Signal(QPoint)
    color_picked = Signal(QColor)

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document; self.zoom = 1.0; self.pan = QPointF(); self.color = QColor("#111111")
        self.brush_size = 8; self.opacity = 100; self.tool = Tool.BRUSH; self._drawing = False; self._panning = False
        self._last_canvas_pos: QPoint | None = None; self._start_canvas_pos: QPoint | None = None; self._last_pan_pos = QPointF(); self.selection_rect: QRect | None = None
        self.setMouseTracking(True); self.setMinimumSize(500, 400); self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_tool(self, tool: Tool | str) -> None:
        self.tool = Tool(tool); self._drawing = False; self._last_canvas_pos = None; self._start_canvas_pos = None; self.update()

    def set_color(self, color: QColor) -> None: self.color = QColor(color)
    def set_brush_size(self, size: int) -> None: self.brush_size = max(1, min(500, int(size)))
    def set_opacity(self, opacity: int) -> None: self.opacity = max(1, min(100, int(opacity)))

    def set_zoom(self, zoom: float) -> None:
        self.zoom = max(0.05, min(8.0, zoom)); self.zoom_changed.emit(round(self.zoom * 100)); self.update()
    def zoom_in(self) -> None: self.set_zoom(self.zoom * 1.15)
    def zoom_out(self) -> None: self.set_zoom(self.zoom / 1.15)
    def reset_view(self) -> None: self.zoom = 1.0; self.pan = QPointF(); self.zoom_changed.emit(100); self.update()
    def fit_to_window(self) -> None:
        if self.document.width > 0 and self.document.height > 0: self.set_zoom(min((self.width() - 80) / self.document.width, (self.height() - 80) / self.document.height))

    def _image_top_left(self) -> QPointF:
        return QPointF((self.width() - self.document.width * self.zoom) / 2 + self.pan.x(), (self.height() - self.document.height * self.zoom) / 2 + self.pan.y())

    def widget_to_canvas(self, pos: QPointF) -> QPoint | None:
        top_left = self._image_top_left(); x = int((pos.x() - top_left.x()) / self.zoom); y = int((pos.y() - top_left.y()) / self.zoom)
        return QPoint(x, y) if 0 <= x < self.document.width and 0 <= y < self.document.height else None

    @staticmethod
    def _normalized_rect(start: QPoint, end: QPoint) -> QRect: return QRect(start, end).normalized()

    def paintEvent(self, event) -> None:
        painter = QPainter(self); painter.fillRect(self.rect(), QColor("#202124")); top_left = self._image_top_left(); painter.save(); painter.translate(top_left); painter.scale(self.zoom, self.zoom); painter.drawPixmap(0, 0, self.document.composite())
        if self._drawing and self._start_canvas_pos and self._last_canvas_pos and self.tool in {Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE, Tool.SELECT_RECT}:
            painter.setPen(QPen(QColor("#63a4ff") if self.tool == Tool.SELECT_RECT else self._paint_color(), max(1, self.brush_size), Qt.PenStyle.DashLine if self.tool == Tool.SELECT_RECT else Qt.PenStyle.SolidLine)); painter.setBrush(Qt.BrushStyle.NoBrush); rect = self._normalized_rect(self._start_canvas_pos, self._last_canvas_pos)
            if self.tool == Tool.LINE: painter.drawLine(self._start_canvas_pos, self._last_canvas_pos)
            elif self.tool in {Tool.RECTANGLE, Tool.SELECT_RECT}: painter.drawRect(rect)
            else: painter.drawEllipse(rect)
        if self.selection_rect:
            painter.setPen(QPen(QColor("#63a4ff"), 1, Qt.PenStyle.DashLine)); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawRect(self.selection_rect)
        painter.restore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or (event.button() == Qt.MouseButton.LeftButton and event.modifiers() & Qt.KeyboardModifier.SpaceModifier): self._panning = True; self._last_pan_pos = event.position(); return
        if event.button() != Qt.MouseButton.LeftButton: return
        point = self.widget_to_canvas(event.position())
        if point is None: return
        if self.tool == Tool.EYEDROPPER:
            color = self.document.composite().toImage().pixelColor(point); self.set_color(color); self.color_picked.emit(color); return
        if self.document.active_layer.locked: return
        self.action_started.emit(); self._drawing = True; self._last_canvas_pos = point; self._start_canvas_pos = point
        if self.tool == Tool.FILL: self._flood_fill(point); self._finish_action()
        elif self.tool in {Tool.BRUSH, Tool.ERASER}: self._draw_segment(point, point)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.position() - self._last_pan_pos; self.pan += delta; self._last_pan_pos = event.position(); self.update(); return
        point = self.widget_to_canvas(event.position())
        if point is not None: self.cursor_position_changed.emit(point)
        if not self._drawing or point is None: return
        if self.tool in {Tool.BRUSH, Tool.ERASER} and self._last_canvas_pos is not None: self._draw_segment(self._last_canvas_pos, point)
        self._last_canvas_pos = point; self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._panning: self._panning = False; return
        if event.button() != Qt.MouseButton.LeftButton or not self._drawing: return
        if self._start_canvas_pos and self._last_canvas_pos:
            if self.tool in {Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE}: self._draw_shape(self._start_canvas_pos, self._last_canvas_pos)
            elif self.tool == Tool.SELECT_RECT: self.selection_rect = self._normalized_rect(self._start_canvas_pos, self._last_canvas_pos)
        self._finish_action()

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            self.zoom_in() if event.angleDelta().y() > 0 else self.zoom_out(); event.accept(); return
        super().wheelEvent(event)

    def _paint_color(self) -> QColor:
        color = QColor(self.color); color.setAlpha(round(255 * self.opacity / 100)); return color

    def _draw_segment(self, start: QPoint, end: QPoint) -> None:
        painter = QPainter(self.document.active_layer.pixmap); painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear if self.tool == Tool.ERASER else QPainter.CompositionMode.CompositionMode_SourceOver); color = QColor(0, 0, 0, 255) if self.tool == Tool.ERASER else self._paint_color(); painter.setRenderHint(QPainter.RenderHint.Antialiasing, True); painter.setPen(QPen(color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); painter.drawLine(start, end); painter.end(); self.update()

    def _draw_shape(self, start: QPoint, end: QPoint) -> None:
        painter = QPainter(self.document.active_layer.pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing, True); painter.setPen(QPen(self._paint_color(), self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)); rect = self._normalized_rect(start, end)
        if self.tool == Tool.LINE: painter.drawLine(start, end)
        elif self.tool == Tool.RECTANGLE: painter.drawRect(rect)
        elif self.tool == Tool.ELLIPSE: painter.drawEllipse(rect)
        painter.end()

    def _flood_fill(self, point: QPoint) -> None:
        image = self.document.active_layer.pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32); target = image.pixelColor(point); replacement = self._paint_color()
        if target == replacement: return
        queue = deque([(point.x(), point.y())]); visited: set[tuple[int, int]] = set(); width, height = image.width(), image.height()
        while queue:
            x, y = queue.popleft()
            if (x, y) in visited or not (0 <= x < width and 0 <= y < height) or image.pixelColor(x, y) != target: continue
            visited.add((x, y)); image.setPixelColor(x, y, replacement); queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))
        self.document.active_layer.pixmap = QPixmap.fromImage(image); self.update()

    def _finish_action(self) -> None:
        self._drawing = False; self._last_canvas_pos = None; self._start_canvas_pos = None; self.document_changed.emit(); self.update()
