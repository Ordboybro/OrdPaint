from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut


def _set_shortcut(window, name: str, shortcut: str) -> None:
    action = getattr(window, name, None)
    if action is not None:
        action.setShortcut(QKeySequence(shortcut))
        action.setShortcutVisibleInContextMenu(True)


def install(window) -> None:
    """Install a single documented shortcut map after all optional actions exist."""
    shortcuts = {
        "new_action": "Ctrl+N",
        "open_action": "Ctrl+O",
        "save_action": "Ctrl+S",
        "save_as_action": "Ctrl+Shift+S",
        "undo_action": "Ctrl+Z",
        "redo_action": "Ctrl+Y",
        "copy_action": "Ctrl+C",
        "cut_action": "Ctrl+X",
        "paste_action": "Ctrl+V",
        "select_all_action": "Ctrl+A",
        "deselect_action": "Ctrl+D",
        "delete_action": "Delete",
        "reset_view_action": "1",
        "fit_view_action": "2",
        "begin_transform_action": "Ctrl+T",
        "commit_transform_action": "Return",
        "cancel_transform_action": "Escape",
        "flip_horizontal_action": "Ctrl+Shift+H",
        "flip_vertical_action": "Ctrl+Shift+V",
        "rotate_clockwise_action": "Ctrl+Shift+R",
        "rotate_counterclockwise_action": "Ctrl+Shift+L",
    }
    for name, shortcut in shortcuts.items():
        _set_shortcut(window, name, shortcut)

    canvas = getattr(window, "canvas", None)
    if canvas is not None:
        if hasattr(canvas, "reset_view"):
            reset = QShortcut(QKeySequence("0"), window)
            reset.activated.connect(canvas.reset_view)
            window._ordpaint_reset_view_shortcut = reset
        if hasattr(canvas, "fit_to_window"):
            fit = QShortcut(QKeySequence("2"), window)
            fit.activated.connect(canvas.fit_to_window)
            window._ordpaint_fit_view_shortcut = fit

    # Make the map discoverable from the application object for future shortcut settings UI.
    window.ordpaint_shortcuts = dict(shortcuts) | {"reset_view": "0", "fit_view": "2"}
