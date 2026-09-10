from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QWidget

from ordpaint.ui.keyboard_polish import install


def test_editor_shortcuts_are_unique_and_documented(qapp) -> None:
    window = QWidget()
    names = (
        "new_action", "open_action", "save_action", "save_as_action", "undo_action", "redo_action",
        "copy_action", "cut_action", "paste_action", "select_all_action", "deselect_action", "delete_action",
        "reset_view_action", "fit_view_action", "begin_transform_action", "commit_transform_action",
        "cancel_transform_action", "flip_horizontal_action", "flip_vertical_action", "rotate_clockwise_action",
        "rotate_counterclockwise_action",
    )
    for name in names:
        setattr(window, name, QAction(window))

    install(window)
    shortcuts = [getattr(window, name).shortcut().toString() for name in names]
    assert len(shortcuts) == len(set(shortcuts))
    assert shortcuts[:12] == [
        "Ctrl+N", "Ctrl+O", "Ctrl+S", "Ctrl+Shift+S", "Ctrl+Z", "Ctrl+Y",
        "Ctrl+C", "Ctrl+X", "Ctrl+V", "Ctrl+A", "Ctrl+D", "Del",
    ]
    assert window.reset_view_action.shortcut() == QKeySequence("1")
    assert window.fit_view_action.shortcut() == QKeySequence("2")
    assert window.ordpaint_shortcuts["begin_transform_action"] == "Ctrl+T"
