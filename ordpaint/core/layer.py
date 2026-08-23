from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


@dataclass
class Layer:
    name: str
    pixmap: QPixmap
    visible: bool = True
    opacity: int = 100
    blend_mode: Qt.CompositionMode = Qt.CompositionMode_SourceOver
    locked: bool = False

    def copy(self) -> "Layer":
        return Layer(
            name=self.name,
            pixmap=QPixmap(self.pixmap),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            locked=self.locked,
        )
