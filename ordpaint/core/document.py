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
        if self.width < 1 or self.height < 1:
            raise ValueError("Document dimensions must be positive")
        if not self.layers:
            self.add_layer("Layer 1")
        self.active_index = max(0, min(self.active_index, len(self.layers) - 1))

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

    def add_layer(self, name: str | None = None, index: int | None = None) -> Layer:
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        layer = Layer(name or f"Layer {len(self.layers) + 1}", pixmap)
        if index is None:
            index = len(self.layers)
        index = max(0, min(index, len(self.layers)))
        self.layers.insert(index, layer)
        self.active_index = index
        return layer

    def duplicate_active_layer(self) -> Layer:
        duplicate = self.active_layer.copy()
        duplicate.name = self.unique_name(f"{duplicate.name} copy")
        self.layers.insert(self.active_index + 1, duplicate)
        self.active_index += 1
        return duplicate

    def remove_active_layer(self) -> bool:
        if len(self.layers) <= 1:
            return False
        self.layers.pop(self.active_index)
        self.active_index = min(self.active_index, len(self.layers) - 1)
        return True

    def set_active_index(self, index: int) -> None:
        if not 0 <= index < len(self.layers):
            raise IndexError("Layer index out of range")
        self.active_index = index

    def rename_active_layer(self, name: str) -> None:
        name = name.strip()
        if name:
            self.active_layer.name = name

    def set_layer_visibility(self, index: int, visible: bool) -> None:
        self.layers[index].visible = bool(visible)

    def set_layer_opacity(self, index: int, opacity: int) -> None:
        self.layers[index].opacity = max(0, min(100, int(opacity)))

    def set_layer_locked(self, index: int, locked: bool) -> None:
        self.layers[index].locked = bool(locked)

    def move_active_layer(self, offset: int) -> bool:
        target = self.active_index + offset
        if not 0 <= target < len(self.layers):
            return False
        self.layers[self.active_index], self.layers[target] = self.layers[target], self.layers[self.active_index]
        self.active_index = target
        return True

    def merge_active_down(self) -> bool:
        if self.active_index <= 0:
            return False
        lower = self.layers[self.active_index - 1]
        upper = self.active_layer
        painter = QPainter(lower.pixmap)
        painter.setOpacity(max(0, min(100, upper.opacity)) / 100)
        painter.setCompositionMode(upper.blend_mode)
        painter.drawPixmap(0, 0, upper.pixmap)
        painter.end()
        self.layers.pop(self.active_index)
        self.active_index -= 1
        return True

    def merge_visible(self) -> bool:
        visible_indices = [index for index, layer in enumerate(self.layers) if layer.visible]
        if len(visible_indices) <= 1:
            return False

        base_index = visible_indices[0]
        base = self.layers[base_index]
        result = QPixmap(self.width, self.height)
        result.fill(Qt.GlobalColor.transparent)
        painter = QPainter(result)
        for index in visible_indices:
            layer = self.layers[index]
            painter.setOpacity(max(0, min(100, layer.opacity)) / 100)
            painter.setCompositionMode(layer.blend_mode)
            painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()

        base.pixmap = result
        base.opacity = 100
        base.blend_mode = Qt.CompositionMode.CompositionMode_SourceOver
        for index in reversed(visible_indices[1:]):
            self.layers.pop(index)
            if index < self.active_index:
                self.active_index -= 1
        self.active_index = min(base_index, len(self.layers) - 1)
        return True

    def clear_active_layer(self) -> bool:
        layer = self.active_layer
        if layer.locked:
            return False
        layer.pixmap.fill(Qt.GlobalColor.transparent)
        return True

    def unique_name(self, base: str) -> str:
        names = {layer.name for layer in self.layers}
        if base not in names:
            return base
        number = 2
        while f"{base} {number}" in names:
            number += 1
        return f"{base} {number}"

    def composite(self, background: QColor | None = None) -> QPixmap:
        result = QPixmap(self.width, self.height)
        result.fill(background if background is not None else QColor("white"))
        painter = QPainter(result)
        for layer in self.layers:
            if not layer.visible:
                continue
            painter.setOpacity(max(0, min(100, layer.opacity)) / 100)
            painter.setCompositionMode(layer.blend_mode)
            painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        return result
