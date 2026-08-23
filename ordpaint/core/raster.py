from __future__ import annotations

from collections import deque

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QPixmap


def draw_line(
    pixmap: QPixmap,
    start: QPoint,
    end: QPoint,
    color: QColor,
    size: int,
    *,
    opacity: int = 100,
    erase: bool = False,
    clip: QRect | None = None,
) -> None:
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    if clip is not None:
        painter.setClipRect(clip)
    painter.setCompositionMode(
        QPainter.CompositionMode.CompositionMode_Clear if erase else QPainter.CompositionMode.CompositionMode_SourceOver
    )
    draw_color = QColor(color)
    draw_color.setAlpha(round(draw_color.alpha() * max(0, min(100, opacity)) / 100))
    if erase:
        draw_color = QColor(0, 0, 0, 255)
    painter.setPen(
        QPen(
            draw_color,
            max(1, int(size)),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    painter.drawLine(start, end)
    painter.end()


def draw_shape(
    pixmap: QPixmap,
    tool: str,
    start: QPoint,
    end: QPoint,
    color: QColor,
    size: int,
    *,
    opacity: int = 100,
    clip: QRect | None = None,
) -> None:
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    if clip is not None:
        painter.setClipRect(clip)
    draw_color = QColor(color)
    draw_color.setAlpha(round(draw_color.alpha() * max(0, min(100, opacity)) / 100))
    painter.setPen(
        QPen(
            draw_color,
            max(1, int(size)),
            Qt.PenStyle.SolidLine,
            Qt.PenCapStyle.RoundCap,
            Qt.PenJoinStyle.RoundJoin,
        )
    )
    rect = QRect(start, end).normalized()
    if tool == "line":
        painter.drawLine(start, end)
    elif tool == "rectangle":
        painter.drawRect(rect)
    elif tool == "ellipse":
        painter.drawEllipse(rect)
    painter.end()


def clear_rect(pixmap: QPixmap, rect: QRect) -> None:
    painter = QPainter(pixmap)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    painter.fillRect(rect, Qt.GlobalColor.transparent)
    painter.end()


def extract(pixmap: QPixmap, rect: QRect) -> QPixmap:
    return pixmap.copy(rect.normalized())


def paste(pixmap: QPixmap, source: QPixmap, position: QPoint, *, opacity: int = 100) -> None:
    painter = QPainter(pixmap)
    painter.setOpacity(max(0, min(100, opacity)) / 100)
    painter.drawPixmap(position, source)
    painter.end()


def flood_fill(
    pixmap: QPixmap,
    point: QPoint,
    replacement: QColor,
    tolerance: int = 0,
    clip: QRect | None = None,
) -> bool:
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    bounds = QRect(0, 0, image.width(), image.height())
    allowed = bounds if clip is None else bounds.intersected(clip)
    if allowed.isEmpty() or not allowed.contains(point):
        return False
    target = image.pixelColor(point)
    if _color_distance(target, replacement) <= tolerance:
        return False

    width, height = image.width(), image.height()
    queue = deque([(point.x(), point.y())])
    visited: set[tuple[int, int]] = set()
    changed = False
    tolerance = max(0, min(255, int(tolerance)))
    while queue:
        x, y = queue.popleft()
        if (x, y) in visited or not (0 <= x < width and 0 <= y < height):
            continue
        if not allowed.contains(QPoint(x, y)):
            continue
        current = image.pixelColor(x, y)
        if _color_distance(current, target) > tolerance:
            continue
        visited.add((x, y))
        image.setPixelColor(x, y, replacement)
        changed = True
        queue.extend(((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)))

    if changed:
        pixmap.swap(QPixmap.fromImage(image))
    return changed


def _color_distance(left: QColor, right: QColor) -> int:
    return max(
        abs(left.red() - right.red()),
        abs(left.green() - right.green()),
        abs(left.blue() - right.blue()),
        abs(left.alpha() - right.alpha()),
    )
