from __future__ import annotations

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter, QPixmap

from ordpaint.ui.canvas import Canvas


def _blend_pixel(before: QColor, after: QColor, coverage: int) -> QColor:
    if coverage >= 255:
        return after
    if coverage <= 0:
        return before
    a = coverage / 255.0
    return QColor(round(before.red() * (1.0 - a) + after.red() * a), round(before.green() * (1.0 - a) + after.green() * a), round(before.blue() * (1.0 - a) + after.blue() * a), round(before.alpha() * (1.0 - a) + after.alpha() * a))


def _stroke_rect(canvas: Canvas, start, end) -> QRect:
    radius = max(2, int(getattr(canvas, "brush_size", 1) * 0.5) + 2)
    left = min(start.x(), end.x()) - radius
    top = min(start.y(), end.y()) - radius
    right = max(start.x(), end.x()) + radius
    bottom = max(start.y(), end.y()) + radius
    return QRect(left, top, right - left + 1, bottom - top + 1).intersected(QRect(0, 0, canvas.document.width, canvas.document.height))


def _mask_region(before: QPixmap, after: QPixmap, canvas: Canvas, rect: QRect) -> QPixmap:
    selection = canvas.selection
    before_image = before.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    after_image = after.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(rect.height()):
        for x in range(rect.width()):
            coverage = selection.coverage(QPoint(rect.x() + x, rect.y() + y))
            if coverage != 255:
                after_image.setPixelColor(x, y, _blend_pixel(before_image.pixelColor(x, y), after_image.pixelColor(x, y), coverage))
    return QPixmap.fromImage(after_image)


def install() -> None:
    if getattr(Canvas, "_ordpaint_selection_clip_installed", False):
        return
    original_draw_segment = Canvas._draw_segment
    original_delete = Canvas.delete_selection
    original_copy = Canvas.copy_selection

    def draw_segment(self, start, end):
        if not self.selection.active:
            original_draw_segment(self, start, end)
            return
        rect = _stroke_rect(self, start, end)
        if rect.isEmpty():
            return
        layer = self.document.active_layer
        before = layer.pixmap.copy(rect)
        original_draw_segment(self, start, end)
        after = layer.pixmap.copy(rect)
        masked = _mask_region(before, after, self, rect)
        painter = QPainter(layer.pixmap)
        painter.drawPixmap(rect.topLeft(), masked)
        painter.end()
        self.document.touch()
        self.document_changed.emit()

    def delete_selection(self):
        if not self.selection.active:
            return original_delete(self)
        layer = self.document.active_layer
        if layer.locked:
            return False
        rect = self.selection.bounding_rect().intersected(QRect(0, 0, self.document.width, self.document.height))
        if rect.isEmpty():
            return False
        image = layer.pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
        for y in range(rect.height()):
            for x in range(rect.width()):
                coverage = self.selection.coverage(QPoint(rect.x() + x, rect.y() + y))
                if coverage:
                    pixel = image.pixelColor(rect.x() + x, rect.y() + y)
                    pixel.setAlpha(round(pixel.alpha() * (1.0 - coverage / 255.0)))
                    image.setPixelColor(rect.x() + x, rect.y() + y, pixel)
        self.action_started.emit()
        layer.pixmap = QPixmap.fromImage(image)
        self.document.touch()
        self.document_changed.emit()
        self.update()
        return True

    def copy_selection(self):
        if not self.selection.active:
            return original_copy(self)
        rect = self.selection.bounding_rect()
        image = self.document.active_layer.pixmap.toImage().copy(rect)
        mask = self.selection
        for y in range(image.height()):
            for x in range(image.width()):
                coverage = mask.coverage(QPoint(rect.x() + x, rect.y() + y))
                pixel = image.pixelColor(x, y)
                pixel.setAlpha(round(pixel.alpha() * coverage / 255.0))
                image.setPixelColor(x, y, pixel)
        QGuiApplication.clipboard().setImage(image)
        return True

    Canvas._draw_segment = draw_segment
    Canvas.delete_selection = delete_selection
    Canvas.copy_selection = copy_selection
    Canvas._ordpaint_selection_clip_installed = True
