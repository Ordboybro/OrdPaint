from pathlib import Path

from PySide6.QtGui import QColor, QPainter

from ordpaint.core.document import Document
from ordpaint.core.layer_tree import LayerGroup
from ordpaint.core.project import load_project, save_project


def test_nested_group_is_part_of_composite_and_copy(qt_app):
    document = Document(8, 8)
    top = document.add_layer("Top")
    group = document.add_group("Characters")
    document.move_node(top, group)
    painter = QPainter(top.pixmap)
    painter.fillRect(1, 1, 2, 2, QColor("red"))
    painter.end()

    composite = document.composite(QColor(0, 0, 0, 0)).toImage()
    assert composite.pixelColor(1, 1).red() > 200
    assert document.layer_tree.parent_of(top) is group

    copied = document.copy()
    copied_top = next(layer for layer in copied.layers if layer.name == "Top")
    copied_group = next(node for node in copied.layer_tree.children if isinstance(node, LayerGroup))
    assert copied.layer_tree.parent_of(copied_top) is copied_group
    assert copied_top is not top


def test_nested_group_roundtrip(tmp_path: Path, qt_app):
    document = Document(8, 8)
    layer = document.add_layer("Paint")
    outer = document.add_group("Outer")
    inner = document.add_group("Inner", outer)
    document.move_node(layer, inner)
    outer.opacity = 73
    inner.locked = True

    path = tmp_path / "groups.ordpaint"
    save_project(document, path)
    restored = load_project(path)

    assert len(restored.layers) == 2
    outer2 = next(node for node in restored.layer_tree.children if isinstance(node, LayerGroup))
    inner2 = next(node for node in outer2.children if isinstance(node, LayerGroup))
    assert outer2.opacity == 73
    assert inner2.locked is True
    assert restored.layer_tree.parent_of(restored.layers[1]) is inner2
