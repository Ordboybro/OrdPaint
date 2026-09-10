from __future__ import annotations

from dataclasses import dataclass, field

from PySide6.QtGui import QPainter, QPixmap

from .layer import Layer


@dataclass
class LayerGroup:
    """Nested layer container used by the layer workspace."""

    name: str
    children: list[Layer | "LayerGroup"] = field(default_factory=list)
    visible: bool = True
    opacity: int = 100
    locked: bool = False

    def __post_init__(self) -> None:
        self.name = self.name.strip() or "Group"
        self.opacity = max(0, min(100, int(self.opacity)))

    @property
    def is_group(self) -> bool:
        return True

    def add(self, node: Layer | "LayerGroup", index: int | None = None) -> None:
        if node is self:
            raise ValueError("A group cannot contain itself")
        if self.contains(node):
            raise ValueError("Cannot move a group into its own descendant")
        if index is None:
            self.children.append(node)
        else:
            self.children.insert(max(0, min(index, len(self.children))), node)

    def remove(self, node: Layer | "LayerGroup") -> bool:
        try:
            self.children.remove(node)
        except ValueError:
            return False
        return True

    def contains(self, node: Layer | "LayerGroup") -> bool:
        if node in self.children:
            return True
        return any(isinstance(child, LayerGroup) and child.contains(node) for child in self.children)

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
        return LayerGroup(
            name=self.name,
            children=[child.copy() for child in self.children],
            visible=self.visible,
            opacity=self.opacity,
            locked=self.locked,
        )


@dataclass
class LayerTree:
    """Rooted hierarchy with safe drag/drop-style moves and group properties."""

    children: list[Layer | LayerGroup] = field(default_factory=list)

    def add_group(self, name: str = "Group", parent: LayerGroup | None = None) -> LayerGroup:
        group = LayerGroup(name)
        (parent.children if parent is not None else self.children).append(group)
        return group

    def add_layer(self, layer: Layer, parent: LayerGroup | None = None, index: int | None = None) -> None:
        target = parent.children if parent is not None else self.children
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
                    if result is not None or child.contains(node):
                        return result if result is not None else child
            return None

        return find(self.children, None)

    def detach(self, node: Layer | LayerGroup) -> bool:
        parent = self.parent_of(node)
        target = parent.children if parent is not None else self.children
        try:
            target.remove(node)
            return True
        except ValueError:
            return False

    def move(self, node: Layer | LayerGroup, parent: LayerGroup | None, index: int | None = None) -> None:
        if isinstance(node, LayerGroup) and parent is not None and (parent is node or node.contains(parent)):
            raise ValueError("Cannot move a group into itself or its descendants")
        if not self.detach(node):
            raise ValueError("Node is not in this tree")
        target = parent.children if parent is not None else self.children
        if index is None:
            target.append(node)
        else:
            target.insert(max(0, min(index, len(target))), node)

    def set_group_properties(
        self,
        group: LayerGroup,
        *,
        visible: bool | None = None,
        opacity: int | None = None,
        locked: bool | None = None,
        name: str | None = None,
    ) -> None:
        if visible is not None:
            group.visible = bool(visible)
        if opacity is not None:
            group.opacity = max(0, min(100, int(opacity)))
        if locked is not None:
            group.locked = bool(locked)
        if name is not None and name.strip():
            group.name = name.strip()[:128]

    def composite(self, width: int, height: int) -> QPixmap:
        result = QPixmap(width, height)
        result.fill(0)
        painter = QPainter(result)
        self._paint_children(painter, self.children)
        painter.end()
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
            painter.setOpacity(child.opacity / 100)
            painter.setCompositionMode(child.blend_mode)
            painter.drawPixmap(0, 0, child.pixmap)
            painter.restore()
