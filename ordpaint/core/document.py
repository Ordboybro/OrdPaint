from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from .layer import Layer


@dataclass
class Document:
    width: int = 1280
    height: int = 720
    layers: list[Layer] = field(default_factory=list)
    active_index: int = 0

    def __post_init__(self) -> None:
        if not self.layers:
            self.add_layer("Layer 1")

    @property
    def active_layer(self) -> Layer:
        return self.layers[self.active_index]

    def copy(self) -> "Document":
        return Document(
            width=self.width,
            height=self.height,
            layers=[layer.copy() for layer in self.layers],
            active_index=self.active_index,
        )

    def add_layer(self, name: str | None = None) -> Layer:
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        layer = Layer(name or f"Layer {len(self.layers) + 1}", pixmap)
        self.layers.append(layer)
        self.active_index = len(self.layers) - 1
        return layer

    def duplicate_active_layer(self) -> Layer:
        duplicate = self.active_layer.copy()
        duplicate.name = f"{duplicate.name} copy"
        self.layers.insert(self.active_index + 1, duplicate)
        self.active_index += 1
        return duplicate

    def remove_active_layer(self) -> bool:
        if len(self.layers) <= 1:
            return False
        self.layers.pop(self.active_index)
        self.active_index = min(self.active_index, len(self.layers) - 1)
        return True

    def composite(self) -> QPixmap:
        result = QPixmap(self.width, self.height)
        result.fill(QColor("white"))
        painter = QPainter(result)
        for layer in self.layers:
            if not layer.visible:
                continue
            painter.setOpacity(max(0, min(100, layer.opacity)) / 100)
            painter.setCompositionMode(layer.blend_mode)
            painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        return result
