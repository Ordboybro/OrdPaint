from PySide6.QtCore import QPoint, QRect

from ordpaint.core.selection import Selection, SelectionMode


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


def test_selection_add_and_intersect():
    selection = Selection()
    selection.set_rect(QRect(0, 0, 20, 20))
    selection.set_rect(QRect(10, 10, 20, 20), SelectionMode.ADD)
    assert selection.rect == QRect(0, 0, 30, 30)
    selection.set_rect(QRect(5, 5, 10, 10), SelectionMode.INTERSECT)
    assert selection.rect == QRect(5, 5, 10, 10)


def test_selection_subtract_and_clamp():
    selection = Selection()
    selection.set_rect(QRect(0, 0, 20, 20))
    selection.set_rect(QRect(0, 0, 5, 20), SelectionMode.SUBTRACT)
    assert selection.active
    assert selection.rect.width() == 15

    selection.set_rect(QRect(-10, -10, 30, 30))
    selection.clamp(10, 10)
    assert selection.rect == QRect(0, 0, 10, 10)
