from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QMessageBox

from ordpaint.core.image_ops import crop_document, flip_document, grayscale_document, invert_document


def _find_menu(window, title: str):
    for menu in window.menuBar().findChildren(QMenu):
        if menu.title() == title:
            return menu
    return None


def install(window) -> None:
    if getattr(window, "_ordpaint_image_ops", False):
        return
    menu = _find_menu(window, "Изображение")
    if menu is None:
        menu = window.menuBar().addMenu("Изображение")

    def apply(name: str, operation) -> None:
        window._push_history()
        try:
            changed = operation()
        except ValueError as exc:
            window.history.undo(window.document)
            QMessageBox.warning(window, name, str(exc))
            return
        if changed:
            window.dirty = True
            window._refresh_layers()
            window.canvas.update()
            window._update_window_title()

    def crop() -> None:
        rect = window.canvas.selection_rect
        if rect is None or rect.isEmpty():
            QMessageBox.information(window, "Кадрирование", "Сначала выделите область для кадрирования.")
            return
        apply("Кадрирование", lambda: crop_document(window.document, rect))
        window.canvas.deselect()

    crop_action = QAction("Кадрировать по выделению", window, shortcut="Ctrl+Shift+C")
    crop_action.triggered.connect(crop)
    menu.addSeparator()
    menu.addAction(crop_action)

    operations = (
        ("Отразить по горизонтали", "Ctrl+Alt+H", lambda: flip_document(window.document, horizontal=True)),
        ("Отразить по вертикали", "Ctrl+Alt+V", lambda: flip_document(window.document, vertical=True)),
        ("Инвертировать цвета", "Ctrl+Alt+N", lambda: invert_document(window.document)),
        ("Чёрно-белое", "Ctrl+Alt+G", lambda: grayscale_document(window.document)),
    )
    for text, shortcut, callback in operations:
        action = QAction(text, window, shortcut=shortcut)
        action.triggered.connect(lambda checked=False, op=callback, label=text: apply(label, op))
        menu.addAction(action)

    window.crop_action = crop_action
    window._ordpaint_image_ops = True
