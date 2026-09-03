from __future__ import annotations

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
        QPainter.CompositionMode.CompositionMode_Clear
        if erase
        else QPainter.CompositionMode.CompositionMode_SourceOver
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
    """Fill a contiguous region using scanline spans with bounded Python memory."""
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)
    bounds = QRect(0, 0, image.width(), image.height())
    allowed = bounds if clip is None else bounds.intersected(clip)
    if allowed.isEmpty() or not allowed.contains(point):
        return False

    tolerance = max(0, min(255, int(tolerance)))
    replacement_rgba = replacement.rgba()
    target_rgba = image.pixel(point)
    if _color_distance_rgba(target_rgba, replacement_rgba) <= tolerance:
        return False

    left_bound = allowed.left()
    right_bound = allowed.right()
    top_bound = allowed.top()
    bottom_bound = allowed.bottom()

    def matches(x: int, y: int) -> bool:
        return _color_distance_rgba(image.pixel(x, y), target_rgba) <= tolerance

    stack: list[tuple[int, int]] = [(point.x(), point.y())]
    changed = False

    while stack:
        seed_x, y = stack.pop()
        if not matches(seed_x, y):
            continue

        left = seed_x
        while left > left_bound and matches(left - 1, y):
            left -= 1

        right = seed_x
        while right < right_bound and matches(right + 1, y):
            right += 1

        for x in range(left, right + 1):
            image.setPixel(x, y, replacement_rgba)
        changed = True

        for next_y in (y - 1, y + 1):
            if not (top_bound <= next_y <= bottom_bound):
                continue
            x = left
            while x <= right:
                while x <= right and not matches(x, next_y):
                    x += 1
                if x > right:
                    break
                run_start = x
                while x <= right and matches(x, next_y):
                    x += 1
                stack.append(((run_start + x - 1) // 2, next_y))

    if changed:
        pixmap.swap(QPixmap.fromImage(image))
    return changed


def _color_distance_rgba(left: int, right: int) -> int:
    return max(
        abs(((left >> 16) & 0xFF) - ((right >> 16) & 0xFF)),
        abs(((left >> 8) & 0xFF) - ((right >> 8) & 0xFF)),
        abs((left & 0xFF) - (right & 0xFF)),
        abs(((left >> 24) & 0xFF) - ((right >> 24) & 0xFF)),
    )
