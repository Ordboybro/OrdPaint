from PySide6.QtCore import Qt

from ordpaint.core.document import Document


NINE_ANCHORS = ("top-left", "top", "top-right", "left", "center", "right", "bottom-left", "bottom", "bottom-right")


def test_resize_canvas_accepts_every_anchor(qt_app):
    for anchor in NINE_ANCHORS:
        document = Document(4, 4)
        assert document.resize_canvas(8, 6, anchor) is True
        assert (document.width, document.height) == (8, 6)
        assert document.active_layer.pixmap.size().width() == 8


def test_resize_canvas_rejects_invalid_anchor(qt_app):
    document = Document(4, 4)
    try:
        document.resize_canvas(8, 8, "invalid")
    except ValueError:
        pass
    else:
        raise AssertionError("invalid anchor must raise ValueError")


def test_scale_fast_and_smooth_resize_all_layers(qt_app):
    for mode in (Qt.TransformationMode.FastTransformation, Qt.TransformationMode.SmoothTransformation):
        document = Document(4, 3)
        document.add_layer("Top")
        assert document.scale_image(8, 6, mode) is True
        assert (document.width, document.height) == (8, 6)
        assert all(layer.pixmap.size() == document.active_layer.pixmap.size() for layer in document.layers)


def test_scale_rejects_oversized_result(qt_app):
    document = Document(4, 4)
    try:
        document.scale_image(100_001, 1_000)
    except ValueError:
        pass
    else:
        raise AssertionError("oversized image must raise ValueError")
