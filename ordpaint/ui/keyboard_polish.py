from __future__ import annotations

from PySide6.QtGui import QKeySequence, QShortcut


def install(window) -> None:
    """Install editor-wide ergonomic shortcuts after all optional actions exist."""
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

    canvas = getattr(window, "canvas", None)
    if canvas is not None and hasattr(canvas, "reset_view"):
        shortcut = QShortcut(QKeySequence("0"), window)
        shortcut.activated.connect(canvas.reset_view)
        window._ordpaint_reset_view_shortcut = shortcut
