from __future__ import annotations

from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPixmap

from ordpaint.ui.canvas import Canvas


def _blend_pixel(before: QColor, after: QColor, coverage: int) -> QColor:
    if coverage >= 255:
        return after
    if coverage <= 0:
        return before
    a = coverage / 255.0
    return QColor(
        round(before.red() * (1.0 - a) + after.red() * a),
        round(before.green() * (1.0 - a) + after.green() * a),
        round(before.blue() * (1.0 - a) + after.blue() * a),
        round(before.alpha() * (1.0 - a) + after.alpha() * a),
    )


def _mask_changed(before: QPixmap, after: QPixmap, canvas: Canvas) -> QPixmap:
    selection = canvas.selection
    rect = selection.bounding_rect().intersected(QRect(0, 0, after.width(), after.height()))
    if rect.isEmpty():
        return before
    before_image = before.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    after_image = after.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            coverage = selection.coverage(QPoint(x, y))
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
        before = QPixmap(self.document.active_layer.pixmap)
        original_draw_segment(self, start, end)
        self.document.active_layer.pixmap = _mask_changed(before, self.document.active_layer.pixmap, self)
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
        for y in range(rect.top(), rect.bottom() + 1):
            for x in range(rect.left(), rect.right() + 1):
                coverage = self.selection.coverage(QPoint(x, y))
                if coverage:
                    pixel = image.pixelColor(x, y)
                    pixel.setAlpha(round(pixel.alpha() * (1.0 - coverage / 255.0)))
                    image.setPixelColor(x, y, pixel)
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
