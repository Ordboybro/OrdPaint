from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QPainter, QPixmap


@dataclass
class Layer:
    name: str
    pixmap: QPixmap
    visible: bool = True
    opacity: int = 100
    blend_mode: QPainter.CompositionMode = QPainter.CompositionMode.CompositionMode_SourceOver
    locked: bool = False

    def __post_init__(self) -> None:
        self.opacity = max(0, min(100, int(self.opacity)))
        self.name = self.name.strip() or "Layer"

    @property
    def editable(self) -> bool:
        """Whether pixel operations are allowed; hidden layers can still be edited."""
        return not self.locked and not self.pixmap.isNull()

    def copy(self) -> "Layer":
        return Layer(
            name=self.name,
            pixmap=QPixmap(self.pixmap),
            visible=self.visible,
            opacity=self.opacity,
            blend_mode=self.blend_mode,
            locked=self.locked,
        )
