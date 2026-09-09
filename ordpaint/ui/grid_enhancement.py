from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen

from ordpaint.ui.canvas import Canvas


def install() -> None:
    """Upgrade the existing grid into a lightweight major/minor grid."""
    if getattr(Canvas, "_ordpaint_grid_enhanced", False):
        return

    def draw_grid(self: Canvas, painter: QPainter, target: QRectF) -> None:
        spacing = self.grid_size * self.zoom
        if spacing < 6:
            return
        painter.save()
        painter.setClipRect(target)
        left = max(0, int((self.rect().left() - target.left()) / self.zoom) - self.grid_size)
        right = min(self.document.width, int((self.rect().right() - target.left()) / self.zoom) + self.grid_size)
        top = max(0, int((self.rect().top() - target.top()) / self.zoom) - self.grid_size)
        bottom = min(self.document.height, int((self.rect().bottom() - target.top()) / self.zoom) + self.grid_size)

        major_step = self.grid_size * 5
        minor_step = max(1, self.grid_size // 5)
        show_minor = self.zoom >= 0.35 and minor_step * self.zoom >= 5
        major_pen = QPen(QColor(116, 128, 144, 145), 1)
        grid_pen = QPen(QColor(104, 116, 132, 82), 1)
        sub_pen = QPen(QColor(104, 116, 132, 42), 1)

        if show_minor:
            first_x = (left // minor_step) * minor_step
            first_y = (top // minor_step) * minor_step
            for x in range(first_x, right + minor_step, minor_step):
                if x % self.grid_size == 0:
                    continue
                wx = target.left() + x * self.zoom
                painter.setPen(sub_pen)
                painter.drawLine(QPointF(wx, target.top()), QPointF(wx, target.bottom()))
            for y in range(first_y, bottom + minor_step, minor_step):
                if y % self.grid_size == 0:
                    continue
                wy = target.top() + y * self.zoom
                painter.setPen(sub_pen)
                painter.drawLine(QPointF(target.left(), wy), QPointF(target.right(), wy))

        first_x = (left // self.grid_size) * self.grid_size
        first_y = (top // self.grid_size) * self.grid_size
        for x in range(first_x, right + self.grid_size, self.grid_size):
            wx = target.left() + x * self.zoom
            painter.setPen(major_pen if x % major_step == 0 else grid_pen)
            painter.drawLine(QPointF(wx, target.top()), QPointF(wx, target.bottom()))
        for y in range(first_y, bottom + self.grid_size, self.grid_size):
            wy = target.top() + y * self.zoom
            painter.setPen(major_pen if y % major_step == 0 else grid_pen)
            painter.drawLine(QPointF(target.left(), wy), QPointF(target.right(), wy))
        painter.restore()

    Canvas._draw_grid = draw_grid
    Canvas._ordpaint_grid_enhanced = True
