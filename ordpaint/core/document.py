from __future__ import annotations

from collections import OrderedDict
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
    revision: int = field(default=0, init=False, repr=False, compare=False)
    _composite_cache: OrderedDict[tuple[int, int, int, int], QPixmap] = field(
        default_factory=OrderedDict, init=False, repr=False, compare=False
    )
    _COMPOSITE_CACHE_LIMIT = 4
    _COMPOSITE_CACHE_MAX_PIXELS = 4_000_000

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("Document dimensions must be positive")
        if not self.layers:
            self.add_layer("Layer 1")
        self.active_index = max(0, min(self.active_index, len(self.layers) - 1))

    @property
    def active_layer(self) -> Layer:
        return self.layers[self.active_index]

    def touch(self) -> None:
        self.revision += 1
        self._composite_cache.clear()

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
        layer = Layer(self.unique_name(name or f"Layer {len(self.layers) + 1}"), pixmap)
        if index is None:
            index = len(self.layers)
        index = max(0, min(index, len(self.layers)))
        self.layers.insert(index, layer)
        self.active_index = index
        self.touch()
        return layer

    def duplicate_active_layer(self) -> Layer:
        duplicate = self.active_layer.copy()
        duplicate.name = self.unique_name(f"{duplicate.name} copy")
        self.layers.insert(self.active_index + 1, duplicate)
        self.active_index += 1
        self.touch()
        return duplicate

    def remove_active_layer(self) -> bool:
        if len(self.layers) <= 1:
            return False
        self.layers.pop(self.active_index)
        self.active_index = min(self.active_index, len(self.layers) - 1)
        self.touch()
        return True

    def set_active_index(self, index: int) -> None:
        if not 0 <= index < len(self.layers):
            raise IndexError("Layer index out of range")
        self.active_index = index

    def rename_layer(self, index: int, name: str) -> bool:
        name = name.strip()[:128]
        if not name:
            return False
        layer = self.layers[index]
        if name == layer.name:
            return False
        names = {item.name for position, item in enumerate(self.layers) if position != index}
        base = name
        number = 2
        while name in names:
            name = f"{base} {number}"
            number += 1
        layer.name = name
        self.touch()
        return True

    def rename_active_layer(self, name: str) -> bool:
        return self.rename_layer(self.active_index, name)

    def set_layer_visibility(self, index: int, visible: bool) -> None:
        visible = bool(visible)
        if self.layers[index].visible != visible:
            self.layers[index].visible = visible
            self.touch()

    def set_layer_opacity(self, index: int, opacity: int) -> None:
        value = max(0, min(100, int(opacity)))
        if self.layers[index].opacity != value:
            self.layers[index].opacity = value
            self.touch()

    def set_layer_blend_mode(self, index: int, blend_mode: QPainter.CompositionMode) -> bool:
        mode = QPainter.CompositionMode(blend_mode)
        if self.layers[index].blend_mode == mode:
            return False
        self.layers[index].blend_mode = mode
        self.touch()
        return True

    def set_layer_locked(self, index: int, locked: bool) -> None:
        locked = bool(locked)
        if self.layers[index].locked != locked:
            self.layers[index].locked = locked
            self.touch()

    def move_active_layer(self, offset: int) -> bool:
        return self.move_layer(self.active_index, self.active_index + offset)

    def move_layer(self, source: int, target: int) -> bool:
        if not 0 <= source < len(self.layers) or not 0 <= target < len(self.layers) or source == target:
            return False
        layer = self.layers.pop(source)
        self.layers.insert(target, layer)
        self.active_index = target
        self.touch()
        return True

    def merge_active_down(self) -> bool:
        if self.active_index <= 0:
            return False
        lower = self.layers[self.active_index - 1]
        upper = self.active_layer
        if lower.locked:
            return False
        painter = QPainter(lower.pixmap)
        painter.setOpacity(max(0, min(100, upper.opacity)) / 100)
        painter.setCompositionMode(upper.blend_mode)
        painter.drawPixmap(0, 0, upper.pixmap)
        painter.end()
        self.layers.pop(self.active_index)
        self.active_index -= 1
        self.touch()
        return True

    def merge_visible(self) -> bool:
        visible_indices = [index for index, layer in enumerate(self.layers) if layer.visible]
        if len(visible_indices) <= 1:
            return False
        base_index = visible_indices[0]
        base = self.layers[base_index]
        if base.locked:
            return False
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
        base.blend_mode = QPainter.CompositionMode.CompositionMode_SourceOver
        for index in reversed(visible_indices[1:]):
            self.layers.pop(index)
            if index < self.active_index:
                self.active_index -= 1
        self.active_index = min(base_index, len(self.layers) - 1)
        self.touch()
        return True

    def clear_active_layer(self) -> bool:
        layer = self.active_layer
        if layer.locked:
            return False
        layer.pixmap.fill(Qt.GlobalColor.transparent)
        self.touch()
        return True

    def unique_name(self, base: str) -> str:
        base = base.strip()[:128] or "Layer"
        names = {layer.name for layer in self.layers}
        if base not in names:
            return base
        number = 2
        while f"{base} {number}" in names:
            number += 1
        return f"{base} {number}"

    def composite(self, background: QColor | None = None) -> QPixmap:
        color = background if background is not None else QColor("white")
        key = (color.red(), color.green(), color.blue(), color.alpha())
        use_cache = self.width * self.height <= self._COMPOSITE_CACHE_MAX_PIXELS
        if use_cache:
            cached = self._composite_cache.get(key)
            if cached is not None:
                self._composite_cache.move_to_end(key)
                return cached.copy()
        result = QPixmap(self.width, self.height)
        result.fill(color)
        painter = QPainter(result)
        for layer in self.layers:
            if not layer.visible:
                continue
            painter.setOpacity(max(0, min(100, layer.opacity)) / 100)
            painter.setCompositionMode(layer.blend_mode)
            painter.drawPixmap(0, 0, layer.pixmap)
        painter.end()
        if use_cache:
            self._composite_cache[key] = result
            self._composite_cache.move_to_end(key)
            while len(self._composite_cache) > self._COMPOSITE_CACHE_LIMIT:
                self._composite_cache.popitem(last=False)
        return result.copy()
