from PySide6.QtCore import QPoint, QRect
from PySide6.QtGui import QColor, QPixmap

from ordpaint.core.brush_engine import BrushEngine, BrushDynamics, BrushPreset, Stabilizer
from ordpaint.core.document import Document
from ordpaint.core.image_ops import crop_document, flip_document
from ordpaint.core.layer import Layer
from ordpaint.core.layer_tree import LayerGroup, LayerTree
from ordpaint.core.selection import Selection, SelectionMode


def test_selection_shapes_and_boolean_modes():
    selection = Selection(32, 32)
    selection.set_ellipse(QRect(4, 4, 12, 12))
    assert selection.active
    assert selection.contains(QPoint(10, 10))
    assert not selection.contains(QPoint(4, 4))
    selection.set_rect(QRect(8, 8, 8, 8), SelectionMode.ADD)
    assert selection.contains(QPoint(9, 9))
    selection.set_rect(QRect(9, 9, 2, 2), SelectionMode.SUBTRACT)
    assert not selection.contains(QPoint(9, 9))
    selection.set_polygon([QPoint(2, 2), QPoint(20, 2), QPoint(2, 20)])
    assert selection.contains(QPoint(4, 4))


def test_lasso_and_intersection():
    selection = Selection(24, 24)
    selection.set_lasso([QPoint(2, 2), QPoint(20, 2), QPoint(20, 20), QPoint(2, 20)])
    selection.set_rect(QRect(0, 0, 8, 8), SelectionMode.INTERSECT)
    assert selection.contains(QPoint(4, 4))
    assert not selection.contains(QPoint(12, 12))


def test_nested_layer_tree_move_and_properties():
    tree = LayerTree()
    group = tree.add_group("Characters")
    nested = tree.add_group("Face", group)
    layer = Layer("Eyes", QPixmap(8, 8))
    tree.add_layer(layer, nested)
    assert tree.parent_of(layer) is nested
    tree.set_group_properties(group, opacity=70, visible=False, locked=True)
    assert (group.opacity, group.visible, group.locked) == (70, False, True)
    tree.move(layer, group)
    assert tree.parent_of(layer) is group


def test_brush_engine_pressure_stabilizer_and_preview():
    engine = BrushEngine()
    engine.preset = BrushPreset("Ink", size=20, opacity=80, dynamics=BrushDynamics())
    size_low, opacity_low = engine.effective_size_opacity(0.2)
    size_high, opacity_high = engine.effective_size_opacity(1.0)
    assert size_high > size_low
    assert opacity_high > opacity_low
    engine.preset = BrushPreset("Stabilized", stabilizer=Stabilizer(0.8))
    engine.begin_stroke(engine.point.__annotations__.get("point", None) or __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(0, 0))
    point = engine.point(__import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(10, 0), 0.5)
    assert 0 < point.x() < 10
    assert engine.preview_points(__import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(0, 0), __import__("PySide6.QtCore", fromlist=["QPointF"]).QPointF(30, 0), 1.0)


def test_crop_and_flip_document():
    document = Document(width=16, height=12)
    document.active_layer.pixmap.fill(QColor("red"))
    assert crop_document(document, QRect(2, 3, 8, 6))
    assert (document.width, document.height) == (8, 6)
    assert flip_document(document, horizontal=True)
