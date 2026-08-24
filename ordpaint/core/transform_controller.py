from __future__ import annotations

from PySide6.QtCore import QPointF, QRect
from PySide6.QtGui import QImage, QPixmap

from .clipboard import crop_image
from .document import Document
from .transform import TransformState


class TransformController:
    """Owns one reversible floating transform for a document.

    Starting or editing a transform never mutates the document. Only ``commit``
    changes pixels/layers, which gives the UI a clean Enter/Escape workflow and
    keeps Undo history to one snapshot per completed transform.
    """

    def __init__(self) -> None:
        self.state: TransformState | None = None

    @property
    def active(self) -> bool:
        return self.state is not None and self.state.active

    def clear(self) -> None:
        self.state = None

    def begin_from_selection(self, document: Document, rect: QRect) -> bool:
        if self.active or rect.isEmpty() or document.active_layer.locked:
            return False
        clipped = rect.intersected(QRect(0, 0, document.width, document.height))
        if clipped.isEmpty():
            return False
        image = crop_image(document.active_layer.pixmap.toImage(), clipped)
        if image.isNull():
            return False
        self.state = TransformState.from_image(
            image,
            QPointF(clipped.x(), clipped.y()),
            source_rect=clipped,
            source_layer_index=document.active_index,
        )
        return True

    def begin_paste(self, image: QImage, position: QPointF) -> bool:
        if image.isNull():
            return False
        self.state = TransformState.from_image(
            image,
            position,
            create_new_layer=True,
        )
        return True

    def commit(self, document: Document, *, layer_name: str = "Pasted") -> bool:
        state = self.state
        if state is None or not state.active:
            return False

        if state.create_new_layer:
            layer = document.add_layer(document.unique_name(layer_name))
            source = layer.pixmap.toImage()
            layer.pixmap = QPixmap.fromImage(state.render_on(source))
        else:
            if state.source_layer_index is None or not 0 <= state.source_layer_index < len(document.layers):
                return False
            layer = document.layers[state.source_layer_index]
            if layer.locked:
                return False
            source = layer.pixmap.toImage()
            layer.pixmap = QPixmap.fromImage(state.render_on(source, clear_source=True))
            document.active_index = state.source_layer_index
            document.touch()

        self.state = None
        return True
