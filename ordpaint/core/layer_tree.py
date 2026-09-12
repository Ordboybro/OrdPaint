from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtGui import QPainter, QPixmap

from .layer import Layer


@dataclass
class LayerGroup:
    name: str
    children: list[Layer | "LayerGroup"] = field(default_factory=list)
    visible: bool = True
    opacity: int = 100
    locked: bool = False

    def __post_init__(self) -> None:
        self.name = self.name.strip()[:128] or "Group"
        self.opacity = max(0, min(100, int(self.opacity)))

    @property
    def is_group(self) -> bool:
        return True

    def add(self, node: Layer | "LayerGroup", index: int | None = None) -> None:
        if node is self or (isinstance(node, LayerGroup) and node.contains(self)):
            raise ValueError("Cannot create a cyclic layer hierarchy")
        if any(child is node for child in self.children):
            raise ValueError("Node is already in this group")
        if index is None:
            self.children.append(node)
        else:
            self.children.insert(max(0, min(index, len(self.children))), node)

    def remove(self, node: Layer | "LayerGroup") -> bool:
        for index, child in enumerate(self.children):
            if child is node:
                self.children.pop(index)
                return True
        return False

    def contains(self, node: Layer | "LayerGroup") -> bool:
        for child in self.children:
            if child is node:
                return True
            if isinstance(child, LayerGroup) and child.contains(node):
                return True
        return False

    def iter_layers(self):
        for child in self.children:
            if isinstance(child, LayerGroup):
                yield from child.iter_layers()
            else:
                yield child

    def iter_nodes(self):
        for child in self.children:
            yield child
            if isinstance(child, LayerGroup):
                yield from child.iter_nodes()

    def copy(self) -> "LayerGroup":
        return LayerGroup(self.name, [child.copy() for child in self.children], self.visible, self.opacity, self.locked)

    def copy_with_layer_map(self, mapping: dict[int, Layer]) -> "LayerGroup":
        copied: list[Layer | LayerGroup] = []
        for child in self.children:
            if isinstance(child, LayerGroup):
                copied.append(child.copy_with_layer_map(mapping))
            else:
                copied.append(mapping[id(child)])
        return LayerGroup(self.name, copied, self.visible, self.opacity, self.locked)


@dataclass
class LayerTree:
    children: list[Layer | LayerGroup] = field(default_factory=list)

    def add_group(self, name: str = "Group", parent: LayerGroup | None = None) -> LayerGroup:
        group = LayerGroup(name)
        if parent is None:
            self.children.append(group)
        else:
            parent.add(group)
        return group

    def add_layer(self, layer: Layer, parent: LayerGroup | None = None, index: int | None = None) -> None:
        target = self.children if parent is None else parent.children
        if index is None:
            target.append(layer)
        else:
            target.insert(max(0, min(index, len(target))), layer)

    def parent_of(self, node: Layer | LayerGroup) -> LayerGroup | None:
        def find(children, parent):
            for child in children:
                if child is node:
                    return parent
                if isinstance(child, LayerGroup):
                    result = find(child.children, child)
                    if result is not None:
                        return result
            return None

        return find(self.children, None)

    def detach(self, node: Layer | LayerGroup) -> bool:
        parent = self.parent_of(node)
        target = parent.children if parent is not None else self.children
        for index, child in enumerate(target):
            if child is node:
                target.pop(index)
                return True
        return False

    def move(self, node: Layer | LayerGroup, parent: LayerGroup | None, index: int | None = None) -> None:
        if isinstance(node, LayerGroup) and parent is not None and (parent is node or node.contains(parent)):
            raise ValueError("Cannot move a group into itself or its descendants")
        old_parent = self.parent_of(node)
        if old_parent is parent:
            siblings = old_parent.children if old_parent is not None else self.children
            old_index = next((i for i, item in enumerate(siblings) if item is node), -1)
            if old_index >= 0 and index is not None and index > old_index:
                index -= 1
        if not self.detach(node):
            raise ValueError("Node is not in this tree")
        target = parent.children if parent is not None else self.children
        if index is None:
            target.append(node)
        else:
            target.insert(max(0, min(index, len(target))), node)

    def copy(self) -> "LayerTree":
        return LayerTree([child.copy() for child in self.children])

    def copy_with_layer_map(self, mapping: dict[int, Layer]) -> "LayerTree":
        children: list[Layer | LayerGroup] = []
        for child in self.children:
            if isinstance(child, LayerGroup):
                children.append(child.copy_with_layer_map(mapping))
            else:
                children.append(mapping[id(child)])
        return LayerTree(children)

    def iter_layers(self):
        for child in self.children:
            if isinstance(child, LayerGroup):
                yield from child.iter_layers()
            else:
                yield child

    def set_group_properties(self, group: LayerGroup, *, visible: bool | None = None, opacity: int | None = None, locked: bool | None = None, name: str | None = None) -> None:
        if visible is not None:
            group.visible = bool(visible)
        if opacity is not None:
            group.opacity = max(0, min(100, int(opacity)))
        if locked is not None:
            group.locked = bool(locked)
        if name is not None and name.strip():
            group.name = name.strip()[:128]

    def paint_into(self, target: QPixmap) -> None:
        painter = QPainter(target)
        self._paint_children(painter, self.children)
        painter.end()

    def composite(self, width: int, height: int) -> QPixmap:
        result = QPixmap(width, height)
        result.fill(0)
        self.paint_into(result)
        return result

    def _paint_children(self, painter: QPainter, children) -> None:
        for child in children:
            if isinstance(child, LayerGroup):
                if not child.visible:
                    continue
                painter.save()
                painter.setOpacity(child.opacity / 100)
                self._paint_children(painter, child.children)
                painter.restore()
                continue
            if not child.visible:
                continue
            painter.save()
            painter.setOpacity(max(0, min(100, child.opacity)) / 100)
            painter.setCompositionMode(child.blend_mode)
            painter.drawPixmap(0, 0, child.pixmap)
            painter.restore()
