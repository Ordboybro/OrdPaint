from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDockWidget, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from ordpaint.core.layer_tree import LayerGroup, LayerTree


class _GroupTreeWidget(QTreeWidget):
    def __init__(self, owner, parent=None) -> None:
        super().__init__(parent)
        self.owner = owner

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        self.owner.sync_model_from_widget()


class LayerGroupDock(QDockWidget):
    """Hierarchy workspace for grouping document layers with drag/drop nesting."""

    def __init__(self, window) -> None:
        super().__init__("Группы слоёв", window)
        self.window = window
        self.tree = LayerTree()
        self.widget = QWidget(self)
        self.layout = QVBoxLayout(self.widget)
        self.list = _GroupTreeWidget(self, self.widget)
        self.list.setHeaderLabels(["Слои и группы"])
        self.list.setDragEnabled(True)
        self.list.setAcceptDrops(True)
        self.list.setDropIndicatorShown(True)
        self.list.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.list.itemChanged.connect(self._item_changed)
        self.layout.addWidget(self.list)
        buttons = QHBoxLayout()
        add_group = QPushButton("+ Группа", self.widget)
        add_group.clicked.connect(self.add_group)
        add_group.setToolTip("Создать вложенную группу")
        buttons.addWidget(add_group)
        self.layout.addLayout(buttons)
        self.setWidget(self.widget)
        self._items: dict[int, LayerGroup | object] = {}
        self.refresh()

    def refresh(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        self.tree = LayerTree()
        for layer in reversed(self.window.document.layers):
            self.tree.add_layer(layer)
        self._rebuild_items()
        self.list.blockSignals(False)

    def _rebuild_items(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        self._items.clear()
        self._append_children(self.list.invisibleRootItem(), self.tree.children)
        self.list.expandAll()
        self.list.blockSignals(False)

    def _append_children(self, parent_item, children) -> None:
        for node in children:
            item = QTreeWidgetItem(parent_item, [getattr(node, "name", "Layer")])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsEditable)
            self._items[id(item)] = node
            if isinstance(node, LayerGroup):
                self._append_children(item, node.children)

    def add_group(self) -> None:
        selected = self.list.currentItem()
        parent = self._items.get(id(selected)) if selected is not None else None
        if parent is not None and not isinstance(parent, LayerGroup):
            parent = None
        self.tree.add_group("Group", parent)
        self._rebuild_items()
        self.list.expandAll()
        self.window.dirty = True
        self.window._update_window_title()

    def _item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if column != 0:
            return
        node = self._items.get(id(item))
        if node is None:
            return
        name = item.text(0).strip()
        if isinstance(node, LayerGroup):
            node.name = name[:128] or "Group"
        else:
            self.window.document.rename_layer(self.window.document.layers.index(node), name)
        self.window.dirty = True
        self.window._update_window_title()

    def sync_model_from_widget(self) -> None:
        self.tree.children = self._read_children(self.list.invisibleRootItem())
        self.sync_to_document()

    def _read_children(self, parent_item) -> list:
        children = []
        for index in range(parent_item.childCount()):
            item = parent_item.child(index)
            node = self._items.get(id(item))
            if node is None:
                continue
            if isinstance(node, LayerGroup):
                node.children = self._read_children(item)
            children.append(node)
        return children

    def sync_to_document(self) -> None:
        layers = list(self.tree.iter_layers())
        if not layers:
            return
        self.window.document.layers = list(reversed(layers))
        self.window.document.active_index = min(self.window.document.active_index, len(self.window.document.layers) - 1)
        self.window.document.touch()
        self.window._refresh_layers()
        self.window.canvas.update()
