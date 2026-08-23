from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ordpaint.core.document import Document


class Canvas(QWidget):
    zoom_changed = Signal(int)
    document_changed = Signal()
    cursor_position_changed = Signal(QPoint)

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.zoom = 1.0
        self.pan = QPointF()
        self.color = QColor("#111111")
        self.brush_size = 8
        self.opacity = 100
        self.eraser = False
        self._drawing = False
        self._panning = False
        self._last_canvas_pos: QPoint | None = None
        self._last_pan_pos = QPointF()
        self.setMouseTracking(True)
        self.setMinimumSize(500, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def set_color(self, color: QColor) -> None:
        self.color = color

    def set_brush_size(self, size: int) -> None:
        self.brush_size = max(1, min(500, int(size)))

    def set_opacity(self, opacity: int) -> None:
        self.opacity = max(1, min(100, int(opacity)))

    def set_eraser(self, enabled: bool) -> None:
        self.eraser = enabled

    def set_zoom(self, zoom: float) -> None:
        self.zoom = max(0.05, min(8.0, zoom))
        self.zoom_changed.emit(round(self.zoom * 100))
        self.update()

    def zoom_in(self) -> None:
        self.set_zoom(self.zoom * 1.15)

    def zoom_out(self) -> None:
        self.set_zoom(self.zoom / 1.15)

    def reset_view(self) -> None:
        self.zoom = 1.0
        self.pan = QPointF()
        self.zoom_changed.emit(100)
        self.update()

    def _image_top_left(self) -> QPointF:
        scaled_w = self.document.width * self.zoom
        scaled_h = self.document.height * self.zoom
        return QPointF(
            (self.width() - scaled_w) / 2 + self.pan.x(),
            (self.height() - scaled_h) / 2 + self.pan.y(),
        )

    def widget_to_canvas(self, pos: QPointF) -> QPoint | None:
        top_left = self._image_top_left()
        x = int((pos.x() - top_left.x()) / self.zoom)
        y = int((pos.y() - top_left.y()) / self.zoom)
        if 0 <= x < self.document.width and 0 <= y < self.document.height:
            return QPoint(x, y)
        return None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#2b2b2b"))
        top_left = self._image_top_left()
        painter.save()
        painter.translate(top_left)
        painter.scale(self.zoom, self.zoom)
        painter.drawPixmap(0, 0, self.document.composite())
        painter.restore()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.SpaceModifier
        ):
            self._panning = True
            self._last_pan_pos = event.position()
            return
        if event.button() != Qt.MouseButton.LeftButton:
            return
        point = self.widget_to_canvas(event.position())
        if point is None or self.document.active_layer.locked:
            return
        self._drawing = True
        self._last_canvas_pos = point
        self._draw_segment(point, point)

    def mouseMoveEvent(self, event) -> None:
        if self._panning:
            delta = event.position() - self._last_pan_pos
            self.pan += delta
            self._last_pan_pos = event.position()
            self.update()
            return
        point = self.widget_to_canvas(event.position())
        if point is not None:
            self.cursor_position_changed.emit(point)
        if not self._drawing or point is None or self._last_canvas_pos is None:
            return
        self._draw_segment(self._last_canvas_pos, point)
        self._last_canvas_pos = point

    def mouseReleaseEvent(self, event) -> None:
        if self._panning:
            self._panning = False
        if event.button() == Qt.MouseButton.LeftButton and self._drawing:
            self._drawing = False
            self._last_canvas_pos = None
            self.document_changed.emit()

    def wheelEvent(self, event) -> None:
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
            return
        super().wheelEvent(event)

    def _draw_segment(self, start: QPoint, end: QPoint) -> None:
        layer = self.document.active_layer
        painter = QPainter(layer.pixmap)
        if self.eraser:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            color = QColor(0, 0, 0, 255)
        else:
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            color = QColor(self.color)
            color.setAlpha(round(255 * self.opacity / 100))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QPen(color, self.brush_size, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        painter.drawLine(start, end)
        painter.end()
        self.update()
