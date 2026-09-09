from __future__ import annotations

from PySide6.QtGui import QKeySequence


def install(window) -> None:
    """Add ergonomic editor shortcuts after all optional actions exist."""
    shortcuts = {
        "flip_horizontal_action": "Ctrl+Shift+H",
        "flip_vertical_action": "Ctrl+Shift+V",
        "rotate_clockwise_action": "Ctrl+Shift+R",
        "rotate_counterclockwise_action": "Ctrl+Shift+L",
        "reset_view_action": "1",
        "fit_view_action": "2",
    }
    for name, shortcut in shortcuts.items():
        action = getattr(window, name, None)
        if action is not None:
            action.setShortcut(QKeySequence(shortcut))
