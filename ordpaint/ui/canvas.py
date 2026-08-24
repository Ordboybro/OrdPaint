from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRect, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFontMetrics, QGuiApplication, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QWidget

from ordpaint.core.clipboard import crop_image
from ordpaint.core.document import Document
from ordpaint.core.raster import draw_line, draw_shape, flood_fill
from ordpaint.core.selection import Selection, SelectionMode
from ordpaint.core.tools import Tool


class Canvas(QWidget):
    """Interactive document viewport, overlays and input layer for the paint engine."""

    action_started = Signal()
    zoom_changed = Signal(int)
    document_changed = Signal()
    cursor_position_changed = Signal(QPoint)
    color_picked = Signal(QColor)

    MIN_ZOOM = 0.05
    MAX_ZOOM = 16.0
    RULER_SIZE = 22

    def __init__(self, document: Document, parent=None) -> None:
        super().__init__(parent)
        self.document = document
        self.zoom = 1.0
        self.pan = QPointF()
        self.color = QColor("#111111")
        self.brush_size = 8
        self.opacity = 100
        self.tool = Tool.BRUSH
        self.selection = Selection()
        self.show_grid = False
        self.show_rulers = True
        self.grid_size = 32

        self._drawing = False
        self._panning = False
        self._space_pan = False
        self._last_canvas_pos: QPoint | None = None
        self._start_canvas_pos: QPoint | None = None
        self._last_pan_pos = QPointF()
        self._hover_canvas_pos: QPoint | None = None
        self._selection_mode = SelectionMode.REPLACE
        self._moving_selection = False
        self._selection_move_anchor: QPoint | None = None
        self._selection_initial_rect: QRect | None = None
        self._selection_dash_offset = 0.0
        self._selection_timer = QTimer(self)
        self._selection_timer.setInterval(90)
        self._selection_timer.timeout.connect(self._advance_selection_animation)
        self._selection_timer.start()

        self.setMouseTracking(True)
        self.setMinimumSize(500, 400)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    @property
    def selection_rect(self) -> QRect | None:
        return self.selection.rect

    def set_document(self, document: Document) -> None:
        self.document = document
        self._cancel_interaction()
        self.selection.clear()
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

    def set_show_grid(self, visible: bool) -> None:
        self.show_grid = bool(visible)
        self.update()

    def set_show_rulers(self, visible: bool) -> None:
        self.show_rulers = bool(visible)
        self.update()

    def set_grid_size(self, size: int) -> None:
        self.grid_size = max(2, min(2048, int(size)))
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
                target = QPointF(
                    top_left.x() + before.x() * self.zoom,
                    top_left.y() + before.y() * self.zoom,
                )
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
        ruler = self.RULER_SIZE if self.show_rulers else 0
        available_width = max(1, self.width() - 80 - ruler)
        available_height = max(1, self.height() - 80 - ruler)
        zoom = min(available_width / self.document.width, available_height / self.document.height)
        self.pan = QPointF()
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, zoom))
        self.zoom_changed.emit(round(self.zoom * 100))
        self.update()

    def select_all(self) -> None:
        self.selection.select_all(self.document.width, self.document.height)
        self.set_tool(Tool.SELECT_RECT)
        self.update()

    def deselect(self) -> None:
        self.selection.clear()
        self.update()

    def set_selection_mode(self, mode: SelectionMode) -> None:
        self._selection_mode = SelectionMode(mode)

    def delete_selection(self) -> bool:
        rect = self.selection.rect
        layer = self.document.active_layer
        if not rect or layer.locked:
            return False
        self.action_started.emit()
        image = layer.pixmap.toImage()
        painter = QPainter(image)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
        painter.fillRect(rect, Qt.GlobalColor.transparent)
        painter.end()
        layer.pixmap = QPixmap.fromImage(image)
        self.document.touch()
        self.document_changed.emit()
        self.update()
        return True

    def copy_selection(self) -> bool:
        rect = self.selection.rect
        if not rect:
            return False
        image = crop_image(self.document.active_layer.pixmap.toImage(), rect)
        if image.isNull():
            return False
        QGuiApplication.clipboard().setImage(image)
        return True

    def cut_selection(self) -> bool:
        if not self.selection.active or self.document.active_layer.locked:
            return False
        if not self.copy_selection():
            return False
        return self.delete_selection()

    def paste_from_clipboard(self) -> bool:
        clipboard = QGuiApplication.clipboard()
        if not clipboard.mimeData().hasImage():
            return False
        image = clipboard.image()
        if image.isNull():
            return False
        if self.selection.active:
            position = self.selection.rect.topLeft()
        else:
            position = QPoint(
                max(0, (self.document.width - image.width()) // 2),
                max(0, (self.document.height - image.height()) // 2),
            )
        self.action_started.emit()
        layer = self.document.add_layer(self.document.unique_name("Pasted"))
        painter = QPainter(layer.pixmap)
        painter.drawImage(position, image)
        painter.end()
        self.document.touch()
        self.document_changed.emit()
        self.selection.set_rect(QRect(position, image.size()))
        self.set_tool(Tool.SELECT_RECT)
        self.update()
        return True

    def move_selection(self, dx: int, dy: int) -> bool:
        if not self.selection.active:
            return False
        old = QRect(self.selection.rect)
        self.selection.move(dx, dy, self.document.width, self.document.height)
        changed = old != self.selection.rect
        if changed:
            self.update()
        return changed

    def _image_top_left(self) -> QPointF:
        return QPointF(
            (self.width() - self.document.width * self.zoom) / 2 + self.pan.x(),
            (self.height() - self.document.height * self.zoom) / 2 + self.pan.y(),
        )

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
        return QRect(
            start,
            QPoint(
                start.x() + (side if dx >= 0 else -side),
                start.y() + (side if dy >= 0 else -side),
            ),
        ).normalized()

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#202124"))
        top_left = self._image_top_left()
        target = QRectF(
            top_left.x(),
            top_left.y(),
            self.document.width * self.zoom,
            self.document.height * self.zoom,
        )
        painter.save()
        painter.setClipRect(self.rect())
        self._draw_checkerboard(painter, target)
        painter.drawPixmap(target, self.document.composite(QColor(0, 0, 0, 0)))
        if self.show_grid:
            self._draw_grid(painter, target)
        painter.restore()

        painter.save()
        painter.translate(top_left)
        painter.scale(self.zoom, self.zoom)
        if self._drawing and self._start_canvas_pos and self._last_canvas_pos and self.tool in {
            Tool.LINE,
            Tool.RECTANGLE,
            Tool.ELLIPSE,
            Tool.SELECT_RECT,
        }:
            self._draw_shape_preview(painter, self._start_canvas_pos, self._last_canvas_pos)
        if self.selection.active:
            self._draw_selection(painter, self.selection.rect)
        painter.restore()

        if self._hover_canvas_pos and self.tool in {Tool.BRUSH, Tool.ERASER}:
            center = self.canvas_to_widget(self._hover_canvas_pos)
            radius = max(0.5, self.brush_size * self.zoom / 2)
            painter.setPen(QPen(QColor("#ffffff"), 1))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(center, radius, radius)

        painter.setPen(QPen(QColor("#4a4d52"), 1))
        painter.drawRect(target)
        if self.show_rulers:
            self._draw_rulers(painter, target)
        painter.end()

    def _draw_checkerboard(self, painter: QPainter, rect: QRectF) -> None:
        size = max(4, min(24, round(12 * self.zoom)))
        left, top = int(rect.left()), int(rect.top())
        right, bottom = int(rect.right()), int(rect.bottom())
        painter.fillRect(rect, QColor("#e8e8e8"))
        for y in range(top - top % size, bottom + size, size):
            for x in range(left - left % size, right + size, size):
                if ((x // size) + (y // size)) % 2 == 0:
                    painter.fillRect(x, y, size, size, QColor("#d0d0d0"))

    def _draw_grid(self, painter: QPainter, target: QRectF) -> None:
        spacing = self.grid_size * self.zoom
        if spacing < 6:
            return
        painter.save()
        painter.setClipRect(target)
        major = QPen(QColor(104, 116, 132, 130), 1)
        minor = QPen(QColor(92, 104, 120, 75), 1)
        show_minor = spacing >= 12
        for x in range(0, self.document.width + 1, self.grid_size):
            widget_x = target.left() + x * self.zoom
            painter.setPen(major if x % (self.grid_size * 5) == 0 else minor)
            if show_minor or x % (self.grid_size * 5) == 0:
                painter.drawLine(QPointF(widget_x, target.top()), QPointF(widget_x, target.bottom()))
        for y in range(0, self.document.height + 1, self.grid_size):
            widget_y = target.top() + y * self.zoom
            painter.setPen(major if y % (self.grid_size * 5) == 0 else minor)
            if show_minor or y % (self.grid_size * 5) == 0:
                painter.drawLine(QPointF(target.left(), widget_y), QPointF(target.right(), widget_y))
        painter.restore()

    @staticmethod
    def _ruler_step(zoom: float) -> int:
        for step in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000):
            if step * zoom >= 42:
                return step
        return 5000

    def _draw_rulers(self, painter: QPainter, target: QRectF) -> None:
        size = self.RULER_SIZE
        step = self._ruler_step(self.zoom)
        major_step = step * 5
        top_rect = QRectF(target.left(), target.top() - size, target.width(), size)
        left_rect = QRectF(target.left() - size, target.top(), size, target.height())
        painter.save()
        painter.fillRect(top_rect, QColor("#171d26"))
        painter.fillRect(left_rect, QColor("#171d26"))
        painter.fillRect(QRectF(target.left() - size, target.top() - size, size, size), QColor("#141a22"))
        painter.setPen(QPen(QColor("#52606f"), 1))
        painter.drawLine(top_rect.bottomLeft(), top_rect.bottomRight())
        painter.drawLine(left_rect.topRight(), left_rect.bottomRight())

        font_metrics = QFontMetrics(painter.font())
        text_pen = QPen(QColor("#9da9b5"))
        tick_pen = QPen(QColor("#657486"), 1)
        painter.setPen(tick_pen)
        for x in range(0, self.document.width + step, step):
            widget_x = target.left() + x * self.zoom
            if widget_x < top_rect.left() - 1 or widget_x > top_rect.right() + 1:
                continue
            is_major = x % major_step == 0
            tick = size if is_major else size * 0.45
            painter.drawLine(
                QPointF(widget_x, top_rect.bottom()),
                QPointF(widget_x, top_rect.bottom() - tick),
            )
            if is_major:
                painter.setPen(text_pen)
                text = str(x)
                painter.drawText(
                    QPointF(widget_x + 3, top_rect.top() + font_metrics.ascent() + 2),
                    text,
                )
                painter.setPen(tick_pen)

        for y in range(0, self.document.height + step, step):
            widget_y = target.top() + y * self.zoom
            if widget_y < left_rect.top() - 1 or widget_y > left_rect.bottom() + 1:
                continue
            is_major = y % major_step == 0
            tick = size if is_major else size * 0.45
            painter.drawLine(
                QPointF(left_rect.right(), widget_y),
                QPointF(left_rect.right() - tick, widget_y),
            )
            if is_major:
                painter.setPen(text_pen)
                text = str(y)
                text_width = font_metrics.horizontalAdvance(text)
                painter.drawText(
                    QPointF(left_rect.right() - text_width - 2, widget_y - 3),
                    text,
                )
                painter.setPen(tick_pen)
        painter.restore()

    def _draw_shape_preview(self, painter: QPainter, start: QPoint, end: QPoint) -> None:
        color = QColor("#63a4ff") if self.tool == Tool.SELECT_RECT else self._paint_color()
        style = Qt.PenStyle.DashLine if self.tool == Tool.SELECT_RECT else Qt.PenStyle.SolidLine
        painter.setPen(
            QPen(
                color,
                max(1, self.brush_size / self.zoom),
                style,
                Qt.PenCapStyle.RoundCap,
                Qt.PenJoinStyle.RoundJoin,
            )
        )
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
        pen = QPen(QColor("#ffffff"), max(1, 1 / self.zoom))
        pen.setStyle(Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([4, 4])
        pen.setDashOffset(self._selection_dash_offset)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(rect)

    def _advance_selection_animation(self) -> None:
        if not self.selection.active:
            return
        self._selection_dash_offset = (self._selection_dash_offset + 1) % 8
        self.update()

    def mousePressEvent(self, event) -> None:
        self.setFocus()
        if event.button() == Qt.MouseButton.MiddleButton or (
            event.button() == Qt.MouseButton.LeftButton
            and event.modifiers() & Qt.KeyboardModifier.SpaceModifier
        ):
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
        if self.tool == Tool.SELECT_RECT:
            modifiers = event.modifiers()
            if self.selection.active and self.selection.contains(point) and not (
                modifiers
                & (
                    Qt.KeyboardModifier.ShiftModifier
                    | Qt.KeyboardModifier.AltModifier
                    | Qt.KeyboardModifier.ControlModifier
                )
            ):
                self._moving_selection = True
                self._selection_move_anchor = QPoint(point)
                self._selection_initial_rect = QRect(self.selection.rect)
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                return
            self._drawing = True
            self._last_canvas_pos = point
            self._start_canvas_pos = point
            if (
                modifiers & Qt.KeyboardModifier.ShiftModifier
                and modifiers & Qt.KeyboardModifier.AltModifier
            ):
                self._selection_mode = SelectionMode.INTERSECT
            elif modifiers & Qt.KeyboardModifier.ShiftModifier:
                self._selection_mode = SelectionMode.ADD
            elif modifiers & Qt.KeyboardModifier.AltModifier:
                self._selection_mode = SelectionMode.SUBTRACT
            else:
                self._selection_mode = SelectionMode.REPLACE
            return
        if self.document.active_layer.locked:
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
        if self._moving_selection:
            if point is None or self._selection_move_anchor is None or self._selection_initial_rect is None:
                return
            moved = QRect(self._selection_initial_rect)
            moved.translate(point - self._selection_move_anchor)
            self.selection.rect = moved
            self.selection.clamp(self.document.width, self.document.height)
            self.update()
            return
        if not self._drawing or point is None:
            self.update()
            return
        if self.tool in {Tool.BRUSH, Tool.ERASER} and self._last_canvas_pos is not None:
            self._draw_segment(self._last_canvas_pos, point)
        self._last_canvas_pos = point
        self.update()

    def mouseReleaseEvent(self, event) -> None:
        if self._panning:
            if (self._space_pan and event.button() == Qt.MouseButton.LeftButton) or (
                not self._space_pan and event.button() == Qt.MouseButton.MiddleButton
            ):
                self._panning = False
                self._space_pan = False
                self.unsetCursor()
            return
        if event.button() == Qt.MouseButton.LeftButton and self._moving_selection:
            self._moving_selection = False
            self._selection_move_anchor = None
            self._selection_initial_rect = None
            self.unsetCursor()
            self.update()
            return
        if event.button() != Qt.MouseButton.LeftButton or not self._drawing:
            return
        if self._start_canvas_pos and self._last_canvas_pos:
            if self.tool in {Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE}:
                self._draw_shape(self._start_canvas_pos, self._last_canvas_pos)
            elif self.tool == Tool.SELECT_RECT:
                rect = (
                    self._constrained_rect(self._start_canvas_pos, self._last_canvas_pos)
                    if self._shift_pressed
                    else self._normalized_rect(self._start_canvas_pos, self._last_canvas_pos)
                )
                self.selection.set_rect(rect, self._selection_mode)
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
        elif self.tool == Tool.SELECT_RECT and event.key() in {
            Qt.Key.Key_Left,
            Qt.Key.Key_Right,
            Qt.Key.Key_Up,
            Qt.Key.Key_Down,
        }:
            delta = {
                Qt.Key.Key_Left: (-1, 0),
                Qt.Key.Key_Right: (1, 0),
                Qt.Key.Key_Up: (0, -1),
                Qt.Key.Key_Down: (0, 1),
            }[event.key()]
            if modifiers & Qt.KeyboardModifier.ShiftModifier:
                delta = (delta[0] * 10, delta[1] * 10)
            self.move_selection(*delta)
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
        draw_line(
            self.document.active_layer.pixmap,
            start,
            end,
            self.color,
            self.brush_size,
            opacity=self.opacity,
            erase=self.tool == Tool.ERASER,
            clip=self.selection.rect,
        )
        self.document.touch()
        self.update()

    def _draw_shape(self, start: QPoint, end: QPoint) -> None:
        draw_shape(
            self.document.active_layer.pixmap,
            self.tool.value,
            start,
            end,
            self.color,
            self.brush_size,
            opacity=self.opacity,
            clip=self.selection.rect,
        )
        self.document.touch()

    def _flood_fill(self, point: QPoint) -> None:
        if flood_fill(
            self.document.active_layer.pixmap,
            point,
            self._paint_color(),
            tolerance=0,
            clip=self.selection.rect,
        ):
            self.document.touch()

    def _cancel_interaction(self) -> None:
        self._drawing = False
        self._panning = False
        self._space_pan = False
        self._moving_selection = False
        self._selection_move_anchor = None
        self._selection_initial_rect = None
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
