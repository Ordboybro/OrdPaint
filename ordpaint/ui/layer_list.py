from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListWidget


class LayerListWidget(QListWidget):
    """Layer list with explicit reorder requests.

    The widget intentionally does not mutate the document itself. After Qt has
    completed an internal drag/drop move it emits the old and new visual rows so
    MainWindow can translate them to document stack indices, push one history
    snapshot and ask the document model to perform the actual mutation.
    """

    reorder_requested = Signal(int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._drag_source_row: int | None = None

    def startDrag(self, supported_actions) -> None:
        self._drag_source_row = self.currentRow()
        super().startDrag(supported_actions)

    def dropEvent(self, event) -> None:
        source_row = self._drag_source_row
        super().dropEvent(event)
        target_row = self.currentRow()
        self._drag_source_row = None
        if source_row is not None and target_row >= 0 and source_row != target_row:
            self.reorder_requested.emit(source_row, target_row)
