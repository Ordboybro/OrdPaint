from PySide6.QtCore import QPoint, QRect

from ordpaint.core.selection import Selection


def test_selection_select_all_and_clear():
    selection = Selection()
    selection.select_all(100, 80)
    assert selection.active
    assert selection.contains(QPoint(50, 40))
    selection.clear()
    assert not selection.active


def test_selection_moves_inside_document():
    selection = Selection()
    selection.set_rect(QRect(80, 70, 20, 20))
    selection.move(30, 30, 100, 100)
    assert selection.rect == QRect(80, 80, 20, 20)
