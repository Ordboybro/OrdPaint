from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from ordpaint.core.tools import Tool
from .canvas_legacy import Canvas as _LegacyCanvas


class Canvas(_LegacyCanvas):
    """Canvas compatibility layer with a PySide6-safe pixmap paint call."""

    def paintEvent(self, event) -> None:
        del event
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#202124"))
        top_left = self._image_top_left()
        target = QRectF(top_left.x(), top_left.y(), self.document.width * self.zoom, self.document.height * self.zoom)
        painter.save()
        painter.setClipRect(self.rect())
        self._draw_checkerboard(painter, target)
        composite = (
            self._transform_preview_composite()
            if self.transform_active
            else self.document.composite(QColor(0, 0, 0, 0))
        )
        painter.drawPixmap(target.toRect(), composite)
        if self.show_grid:
            self._draw_grid(painter, target)
        painter.restore()

        painter.save()
        painter.translate(top_left)
        painter.scale(self.zoom, self.zoom)
        if (
            self._drawing
            and self._start_canvas_pos
            and self._last_canvas_pos
            and self.tool in {Tool.LINE, Tool.RECTANGLE, Tool.ELLIPSE, Tool.SELECT_RECT}
        ):
            self._draw_shape_preview(painter, self._start_canvas_pos, self._last_canvas_pos)
        if self.selection.active and not self.transform_active:
            self._draw_selection(painter, self.selection.rect)
        if self.transform_active:
            self._draw_transform_overlay(painter)
        painter.restore()

        if self._hover_canvas_pos and self.tool in {Tool.BRUSH, Tool.ERASER} and not self.transform_active:
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
