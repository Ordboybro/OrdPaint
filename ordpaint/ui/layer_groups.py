from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox, QDockWidget, QDoubleSpinBox, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget

from ordpaint.core.layer import Layer
from ordpaint.core.layer_tree import LayerGroup
from ordpaint.ui.canvas import Canvas


def _install_group_lock_guard() -> None:
    if getattr(Canvas, "_ordpaint_group_lock_guard", False):
        return
    original_draw = Canvas._draw_segment
    original_shape = getattr(Canvas, "_draw_shape", None)
    original_fill = getattr(Canvas, "_flood_fill", None)
    original_delete = getattr(Canvas, "delete_selection", None)
    original_paste = getattr(Canvas, "paste_from_clipboard", None)
    original_begin_transform = getattr(Canvas, "begin_transform", None)
    original_commit_transform = getattr(Canvas, "commit_transform", None)
    original_flip_horizontal = getattr(Canvas, "flip_transform_horizontal", None)
    original_flip_vertical = getattr(Canvas, "flip_transform_vertical", None)
    original_rotate_clockwise = getattr(Canvas, "rotate_transform_clockwise", None)
    original_rotate_counterclockwise = getattr(Canvas, "rotate_transform_counterclockwise", None)

    def locked(self) -> bool:
        tree = getattr(self.document, "layer_tree", None)
        if tree is None:
            return False
        node = self.document.active_layer
        while True:
            parent = tree.parent_of(node)
            if parent is None:
                return False
            if parent.locked:
                return True
            node = parent

    def draw_segment(self, start, end):
        if locked(self):
            return
        return original_draw(self, start, end)

    Canvas._draw_segment = draw_segment

    if original_shape is not None:
        def draw_shape(self, *args, **kwargs):
            if locked(self):
                return
            return original_shape(self, *args, **kwargs)
        Canvas._draw_shape = draw_shape

    if original_fill is not None:
        def flood_fill(self, *args, **kwargs):
            if locked(self):
                return
            return original_fill(self, *args, **kwargs)
        Canvas._flood_fill = flood_fill

    if original_delete is not None:
        def delete_selection(self, *args, **kwargs):
            if locked(self):
                return False
            return original_delete(self, *args, **kwargs)
        Canvas.delete_selection = delete_selection

    if original_paste is not None:
        def paste_from_clipboard(self, *args, **kwargs):
            if locked(self):
                return False
            return original_paste(self, *args, **kwargs)
        Canvas.paste_from_clipboard = paste_from_clipboard

    if original_begin_transform is not None:
        def begin_transform(self, *args, **kwargs):
            if locked(self):
                return False
            return original_begin_transform(self, *args, **kwargs)
        Canvas.begin_transform = begin_transform

    if original_commit_transform is not None:
        def commit_transform(self, *args, **kwargs):
            if locked(self):
                return False
            return original_commit_transform(self, *args, **kwargs)
        Canvas.commit_transform = commit_transform

    for name, original in (
        ("flip_transform_horizontal", original_flip_horizontal),
        ("flip_transform_vertical", original_flip_vertical),
        ("rotate_transform_clockwise", original_rotate_clockwise),
        ("rotate_transform_counterclockwise", original_rotate_counterclockwise),
    ):
        if original is None:
            continue

        def guarded(self, *args, _original=original, **kwargs):
            if locked(self):
                return False
            return _original(self, *args, **kwargs)

        setattr(Canvas, name, guarded)

    Canvas._ordpaint_group_lock_guard = True


class _GroupTreeWidget(QTreeWidget):
    def __init__(self, owner, parent=None) -> None:
        super().__init__(parent)
        self.owner = owner

    def startDrag(self, supported_actions) -> None:
        self.owner._begin_structure_edit()
        super().startDrag(supported_actions)

    def dropEvent(self, event) -> None:
        super().dropEvent(event)
        self.owner.sync_model_from_widget()


class LayerGroupDock(QDockWidget):
    """Persistent hierarchy workspace backed directly by Document.layer_tree."""

    def __init__(self, window) -> None:
        _install_group_lock_guard()
        super().__init__("Группы слоёв", window)
        self.window = window
        self.widget = QWidget(self)
        layout = QVBoxLayout(self.widget)
        self.list = _GroupTreeWidget(self, self.widget)
        self.list.setHeaderLabels(["Слои и группы"])
        self.list.setDragEnabled(True)
        self.list.setAcceptDrops(True)
        self.list.setDropIndicatorShown(True)
        self.list.setDragDropMode(QTreeWidget.DragDropMode.InternalMove)
        self.list.itemSelectionChanged.connect(self._selection_changed)
        self.list.itemChanged.connect(self._item_changed)
        layout.addWidget(self.list)
        controls = QHBoxLayout()
        add = QPushButton("+ Группа", self.widget)
        remove = QPushButton("−", self.widget)
        add.clicked.connect(self.add_group)
        remove.clicked.connect(self.remove_group)
        controls.addWidget(add)
        controls.addWidget(remove)
        layout.addLayout(controls)
        props = QHBoxLayout()
        props.addWidget(QLabel("Opacity"))
        self.opacity = QDoubleSpinBox(self.widget)
        self.opacity.setRange(0, 100)
        self.opacity.setDecimals(0)
        self.opacity.setSuffix("%")
        self.opacity.valueChanged.connect(self._opacity_changed)
        self.locked = QCheckBox("Lock", self.widget)
        self.locked.toggled.connect(self._lock_changed)
        props.addWidget(self.opacity)
        props.addWidget(self.locked)
        layout.addLayout(props)
        self.setWidget(self.widget)
        self._items: dict[int, Layer | LayerGroup] = {}
        self._updating = False
        self.refresh()

    def _begin_structure_edit(self) -> None:
        push = getattr(self.window, "_push_history", None)
        if callable(push):
            push()

    def refresh(self) -> None:
        self.list.blockSignals(True)
        self.list.clear()
        self._items.clear()
        tree = getattr(self.window.document, "layer_tree", None)
        if tree is not None:
            self._append_children(self.list.invisibleRootItem(), tree.children)
        self.list.expandAll()
        self.list.blockSignals(False)
        self._selection_changed()

    def _append_children(self, parent_item, children) -> None:
        for node in children:
            item = QTreeWidgetItem(parent_item, [getattr(node, "name", "Layer")])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsDropEnabled | Qt.ItemFlag.ItemIsEditable)
            self._items[id(item)] = node
            if isinstance(node, LayerGroup):
                self._append_children(item, node.children)

    def _current_node(self):
        item = self.list.currentItem()
        return self._items.get(id(item)) if item is not None else None

    def add_group(self) -> None:
        self._begin_structure_edit()
        node = self._current_node()
        parent = node if isinstance(node, LayerGroup) else None
        self.window.document.add_group("Group", parent)
        self.window.dirty = True
        self.window._update_window_title()
        self.refresh()

    def remove_group(self) -> None:
        node = self._current_node()
        if not isinstance(node, LayerGroup):
            return
        self._begin_structure_edit()
        self.window.document.remove_group(node)
        self.window.dirty = True
        self.window._update_window_title()
        self.refresh()

    def _item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        if self._updating or column != 0:
            return
        node = self._items.get(id(item))
        if node is None:
            return
        name = item.text(0).strip() or ("Group" if isinstance(node, LayerGroup) else "Layer")
        self._begin_structure_edit()
        if isinstance(node, LayerGroup):
            self.window.document.set_group_properties(node, name=name)
        else:
            self.window.document.rename_layer(self.window.document.layers.index(node), name)
        self.window.dirty = True
        self.window._update_window_title()

    def sync_model_from_widget(self) -> None:
        tree = getattr(self.window.document, "layer_tree", None)
        if tree is None:
            return
        try:
            tree.children = self._read_children(self.list.invisibleRootItem())
            self.window.document._normalize_tree()
            self.window.document._sync_layers_from_tree(preferred_active=self.window.document.active_layer)
            self.window.document.touch()
        except (KeyError, ValueError):
            self.refresh()
            return
        self.window.dirty = True
        self.window._update_window_title()
        self.window._refresh_layers()
        self.window.canvas.update()

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

    def _selection_changed(self) -> None:
        node = self._current_node()
        enabled = isinstance(node, LayerGroup)
        self._updating = True
        self.opacity.setEnabled(enabled)
        self.locked.setEnabled(enabled)
        if enabled:
            self.opacity.setValue(node.opacity)
            self.locked.setChecked(node.locked)
        self._updating = False

    def _opacity_changed(self, value: float) -> None:
        if self._updating:
            return
        node = self._current_node()
        if isinstance(node, LayerGroup):
            self._begin_structure_edit()
            self.window.document.set_group_properties(node, opacity=int(value))
            self.window.dirty = True
            self.window._update_window_title()
            self.window.canvas.update()

    def _lock_changed(self, checked: bool) -> None:
        if self._updating:
            return
        node = self._current_node()
        if isinstance(node, LayerGroup):
            self._begin_structure_edit()
            self.window.document.set_group_properties(node, locked=checked)
            self.window.dirty = True
            self.window._update_window_title()
            self.window.canvas.update()
