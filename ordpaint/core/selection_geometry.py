from __future__ import annotations

from PySide6.QtCore import QPoint, QRect


def rectangle(rect: QRect) -> tuple[QPoint, ...]:
    r = rect.normalized()
    return (r.topLeft(), QPoint(r.right(), r.top()), r.bottomRight(), QPoint(r.left(), r.bottom()))


def ellipse_bounds(rect: QRect) -> QRect:
    return rect.normalized()


def lasso_simplify(points: list[QPoint], tolerance: int = 2) -> list[QPoint]:
    if len(points) < 3:
        return list(points)
    result = [points[0]]
    for point in points[1:]:
        if (point - result[-1]).manhattanLength() >= max(1, tolerance):
            result.append(point)
    if len(result) > 2 and (result[0] - result[-1]).manhattanLength() < tolerance:
        result.pop()
    return result
