from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QPainter, QPixmap

from .layer import Layer
from .layer_tree import LayerGroup, LayerTree


@dataclass
class Document:
    width: int = 1200
    height: int = 800
    layers: list[Layer] = field(default_factory=list)
    active_index: int = 0
    layer_tree: LayerTree | None = field(default=None, repr=False)
    revision: int = field(default=0, init=False, repr=False, compare=False)
    _composite_cache: OrderedDict[tuple[int, int, int, int], QPixmap] = field(default_factory=OrderedDict, init=False, repr=False, compare=False)
    _COMPOSITE_CACHE_LIMIT = 4
    _COMPOSITE_CACHE_MAX_PIXELS = 4_000_000

    def __post_init__(self) -> None:
        if self.width < 1 or self.height < 1:
            raise ValueError("Document dimensions must be positive")
        if not self.layers:
            self.layers = [self._new_layer("Layer 1")]
        old_active = self.layers[max(0, min(self.active_index, len(self.layers) - 1))]
        if self.layer_tree is None:
            self.layer_tree = LayerTree(children=list(self.layers))
        self._normalize_tree()
        self._sync_layers_from_tree(preferred_active=old_active)

    def _new_layer(self, name: str) -> Layer:
        pixmap = QPixmap(self.width, self.height)
        pixmap.fill(Qt.GlobalColor.transparent)
        return Layer(name, pixmap)

    def _normalize_tree(self) -> None:
        assert self.layer_tree is not None
        valid = {id(layer): layer for layer in self.layers}
        seen: set[int] = set()

        def clean_nodes(nodes):
            result = []
            for node in nodes:
                if isinstance(node, LayerGroup):
                    node.children = clean_nodes(node.children)
                    result.append(node)
                elif id(node) in valid and id(node) not in seen:
                    seen.add(id(node))
                    result.append(node)
            return result

        self.layer_tree.children = clean_nodes(self.layer_tree.children)
        for layer in self.layers:
            if id(layer) not in seen:
                self.layer_tree.children.append(layer)
                seen.add(id(layer))

    def _sync_layers_from_tree(self, preferred_active: Layer | None = None) -> None:
        assert self.layer_tree is not None
        flattened = list(self.layer_tree.iter_layers())
        if not flattened:
            raise ValueError("Layer tree must contain at least one layer")
        self.layers = flattened
        if preferred_active is not None and preferred_active in self.layers:
            self.active_index = self.layers.index(preferred_active)
        else:
            self.active_index = max(0, min(self.active_index, len(self.layers) - 1))

    def sync_tree_from_layers(self) -> None:
        """Rebuild only the flat root structure when importing legacy flat data."""
        assert self.layer_tree is not None
        self.layer_tree.children = list(self.layers)
        self._sync_layers_from_tree(preferred_active=self.active_layer)

    @property
    def active_layer(self) -> Layer:
        return self.layers[self.active_index]

    def touch(self) -> None:
        self.revision += 1
        self._composite_cache.clear()

    def copy(self) -> "Document":
        copied_layers = [layer.copy() for layer in self.layers]
        mapping = {id(old): new for old, new in zip(self.layers, copied_layers, strict=True)}
        assert self.layer_tree is not None
        copied_tree = self.layer_tree.copy_with_layer_map(mapping)
        return Document(self.width, self.height, copied_layers, self.active_index, copied_tree)

    def add_layer(self, name: str | None = None, index: int | None = None) -> Layer:
        assert self.layer_tree is not None
        layer = self._new_layer(self.unique_name(name or f"Layer {len(self.layers) + 1}"))
        root_layers = [node for node in self.layer_tree.children if isinstance(node, Layer)]
        if index is None:
            index = len(self.layers)
        root_index = max(0, min(index, len(root_layers)))
        if root_index >= len(root_layers):
            self.layer_tree.add_layer(layer)
        else:
            target = root_layers[root_index]
            position = self.layer_tree.children.index(target)
            self.layer_tree.add_layer(layer, index=position)
        self._sync_layers_from_tree(preferred_active=layer)
        self.touch()
        return layer

    def duplicate_active_layer(self) -> Layer:
        assert self.layer_tree is not None
        source = self.active_layer
        duplicate = source.copy()
        duplicate.name = self.unique_name(f"{duplicate.name} copy")
        parent = self.layer_tree.parent_of(source)
        siblings = parent.children if parent is not None else self.layer_tree.children
        position = siblings.index(source) + 1
        siblings.insert(position, duplicate)
        self._sync_layers_from_tree(preferred_active=duplicate)
        self.touch()
        return duplicate

    def remove_active_layer(self) -> bool:
        if len(self.layers) <= 1:
            return False
        assert self.layer_tree is not None
        removed = self.active_layer
        if not self.layer_tree.detach(removed):
            return False
        self._sync_layers_from_tree()
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
        assert self.layer_tree is not None
        layer = self.layers[source]
        parent = self.layer_tree.parent_of(layer)
        siblings = parent.children if parent is not None else self.layer_tree.children
        sibling_indices = [i for i, node in enumerate(siblings) if isinstance(node, Layer)]
        try:
            old_sibling_index = next(i for i, node in enumerate(siblings) if node is layer)
        except StopIteration:
            return False
        target_sibling_index = max(0, min(len(sibling_indices) - 1, sibling_indices.index(old_sibling_index) + (target - source)))
        target_position = sibling_indices[target_sibling_index]
        node = siblings.pop(old_sibling_index)
        if target_position > old_sibling_index:
            target_position -= 1
        siblings.insert(target_position, node)
        self._sync_layers_from_tree(preferred_active=layer)
        self.touch()
        return True

    def add_group(self, name: str = "Group", parent: LayerGroup | None = None) -> LayerGroup:
        assert self.layer_tree is not None
        group = self.layer_tree.add_group(name, parent)
        self.touch()
        return group

    def remove_group(self, group: LayerGroup) -> bool:
        assert self.layer_tree is not None
        if not self.layer_tree.detach(group):
            return False
        self._sync_layers_from_tree()
        self.touch()
        return True

    def move_node(self, node: Layer | LayerGroup, parent: LayerGroup | None, index: int | None = None) -> bool:
        assert self.layer_tree is not None
        self.layer_tree.move(node, parent, index)
        self._sync_layers_from_tree(preferred_active=node if isinstance(node, Layer) else self.active_layer)
        self.touch()
        return True

    def set_group_properties(self, group: LayerGroup, **kwargs) -> None:
        assert self.layer_tree is not None
        self.layer_tree.set_group_properties(group, **kwargs)
        self.touch()

    def merge_active_down(self) -> bool:
        if self.active_index <= 0:
            return False
        assert self.layer_tree is not None
        upper = self.active_layer
        parent = self.layer_tree.parent_of(upper)
        siblings = parent.children if parent is not None else self.layer_tree.children
        position = siblings.index(upper)
        if position <= 0 or not isinstance(siblings[position - 1], Layer):
            return False
        lower = siblings[position - 1]
        if lower.locked:
            return False
        painter = QPainter(lower.pixmap)
        painter.setOpacity(max(0, min(100, upper.opacity)) / 100)
        painter.setCompositionMode(upper.blend_mode)
        painter.drawPixmap(0, 0, upper.pixmap)
        painter.end()
        siblings.pop(position)
        self._sync_layers_from_tree(preferred_active=lower)
        self.touch()
        return True

    def merge_visible(self) -> bool:
        visible_indices = [index for index, layer in enumerate(self.layers) if layer.visible]
        if len(visible_indices) <= 1:
            return False
        base = self.layers[visible_indices[0]]
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
            layer = self.layers[index]
            self.layer_tree.detach(layer)
        self._sync_layers_from_tree(preferred_active=base)
        self.touch()
        return True

    def clear_active_layer(self) -> bool:
        layer = self.active_layer
        if layer.locked:
            return False
        layer.pixmap.fill(Qt.GlobalColor.transparent)
        self.touch()
        return True

    def resize_canvas(self, width: int, height: int, anchor: str = "center") -> bool:
        width = int(width)
        height = int(height)
        if width < 1 or height < 1 or (width == self.width and height == self.height):
            return False
        if width * height > 100_000_000:
            raise ValueError("Canvas is too large")
        offsets = {
            "top-left": (0, 0),
            "top": ((width - self.width) // 2, 0),
            "top-right": (width - self.width, 0),
            "left": (0, (height - self.height) // 2),
            "center": ((width - self.width) // 2, (height - self.height) // 2),
            "right": (width - self.width, (height - self.height) // 2),
            "bottom-left": (0, height - self.height),
            "bottom": ((width - self.width) // 2, height - self.height),
            "bottom-right": (width - self.width, height - self.height),
        }
        if anchor not in offsets:
            raise ValueError(f"Unknown canvas anchor: {anchor}")
        dx, dy = offsets[anchor]
        offset = QPoint(dx, dy)
        for layer in self.layers:
            resized = QPixmap(width, height)
            resized.fill(Qt.GlobalColor.transparent)
            painter = QPainter(resized)
            painter.drawPixmap(offset, layer.pixmap)
            painter.end()
            layer.pixmap = resized
        self.width = width
        self.height = height
        self.touch()
        return True

    def scale_image(self, width: int, height: int, transformation_mode: Qt.TransformationMode = Qt.TransformationMode.SmoothTransformation) -> bool:
        width = int(width)
        height = int(height)
        if width < 1 or height < 1 or (width == self.width and height == self.height):
            return False
        if width * height > 100_000_000:
            raise ValueError("Image is too large")
        mode = Qt.TransformationMode(transformation_mode)
        for layer in self.layers:
            layer.pixmap = layer.pixmap.scaled(width, height, Qt.AspectRatioMode.IgnoreAspectRatio, mode)
        self.width = width
        self.height = height
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
        assert self.layer_tree is not None
        self.layer_tree.paint_into(result)
        if use_cache:
            self._composite_cache[key] = result
            self._composite_cache.move_to_end(key)
            while len(self._composite_cache) > self._COMPOSITE_CACHE_LIMIT:
                self._composite_cache.popitem(last=False)
        return result.copy()
