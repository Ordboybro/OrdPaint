from PySide6.QtCore import QPoint, QRect

from ordpaint.core.selection_geometry import lasso_simplify, rectangle


def test_rectangle_geometry_is_normalized():
    points = rectangle(QRect(10, 12, -6, -8))
    assert points[0] == QPoint(4, 4)
    assert points[2] == QPoint(9, 11)


def test_lasso_simplify_removes_near_duplicates():
    points = [QPoint(0, 0), QPoint(1, 0), QPoint(4, 0), QPoint(4, 4)]
    result = lasso_simplify(points, tolerance=2)
    assert result == [QPoint(0, 0), QPoint(4, 0), QPoint(4, 4)]
