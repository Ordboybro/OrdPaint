from PySide6.QtCore import QPointF, QRect, QRectF
from PySide6.QtGui import QColor, QImage

from ordpaint.core.transform import TransformHandle, TransformState


def image(width=20, height=10):
    result = QImage(width, height, QImage.Format.Format_ARGB32)
    result.fill(QColor("#00000000"))
    return result


def test_transform_state_starts_with_image_size():
    state = TransformState.from_image(image(), QPointF(5, 7))

    assert state.active
    assert state.rect == QRectF(5, 7, 20, 10)
    assert state.aspect_ratio == 2


def test_move_is_clamped_to_document_bounds():
    state = TransformState.from_image(image(), QPointF(5, 5))
    state.move(QPointF(100, -100), QRectF(0, 0, 50, 40))

    assert state.rect.left() == 30
    assert state.rect.top() == 0


def test_resize_from_south_east_changes_size():
    state = TransformState.from_image(image())
    state.resize(TransformHandle.SOUTH_EAST, QPointF(5, 3))

    assert state.rect.width() == 25
    assert state.rect.height() == 13


def test_resize_with_aspect_ratio_preserves_ratio():
    state = TransformState.from_image(image())
    state.resize(TransformHandle.SOUTH_EAST, QPointF(10, 0), keep_aspect=True)

    assert round(state.rect.width() / state.rect.height(), 6) == 2


def test_resize_respects_minimum_size():
    state = TransformState.from_image(image())
    state.resize(TransformHandle.NORTH_WEST, QPointF(100, 100), minimum_size=4)

    assert state.rect.width() >= 4
    assert state.rect.height() >= 4


def test_flip_horizontal_changes_pixel_order():
    source = image(2, 1)
    source.setPixelColor(0, 0, QColor("#ff0000"))
    source.setPixelColor(1, 0, QColor("#0000ff"))
    state = TransformState.from_image(source)

    state.flip_horizontal()

    assert state.image.pixelColor(0, 0) == QColor("#0000ff")
    assert state.image.pixelColor(1, 0) == QColor("#ff0000")


def test_render_on_can_clear_source_before_drawing_transform():
    source = image(8, 4)
    source.fill(QColor("#ff0000"))
    floating = image(2, 2)
    floating.fill(QColor("#0000ff"))
    state = TransformState.from_image(
        floating,
        QPointF(4, 1),
        source_rect=QRect(0, 0, 2, 2),
    )

    result = state.render_on(source, clear_source=True)

    assert result.pixelColor(0, 0).alpha() == 0
    assert result.pixelColor(4, 1) == QColor("#0000ff")


def test_copy_keeps_source_metadata_independent():
    state = TransformState.from_image(
        image(),
        source_rect=QRect(1, 2, 3, 4),
        source_layer_index=2,
    )
    clone = state.copy()
    clone.rect.moveLeft(10)

    assert state.rect.left() == 0
    assert clone.source_rect == QRect(1, 2, 3, 4)


def test_hit_test_prefers_resize_handles_then_move_area():
    state = TransformState.from_image(image(20, 10), QPointF(10, 20))

    assert state.hit_test(QPointF(10, 20), tolerance=1) == TransformHandle.NORTH_WEST
    assert state.hit_test(QPointF(20, 25), tolerance=1) == TransformHandle.MOVE
    assert state.hit_test(QPointF(0, 0), tolerance=1) is None


def test_handle_positions_cover_all_transform_handles():
    state = TransformState.from_image(image(20, 10), QPointF(10, 20))
    handles = state.handle_positions()

    assert handles[TransformHandle.NORTH] == QPointF(20, 20)
    assert handles[TransformHandle.EAST] == QPointF(30, 25)
    assert handles[TransformHandle.SOUTH_WEST] == QPointF(10, 30)
    assert handles[TransformHandle.MOVE] == QPointF(20, 25)


def test_rotate_clockwise_swaps_dimensions_and_preserves_centre():
    source = image(4, 2)
    state = TransformState.from_image(source, QPointF(10, 20))
    centre = QPointF(state.rect.center())

    state.rotate_90_clockwise()

    assert state.image.width() == 2
    assert state.image.height() == 4
    assert state.rect.width() == 2
    assert state.rect.height() == 4
    assert state.rect.center() == centre


def test_rotate_counterclockwise_swaps_pixel_orientation():
    source = image(2, 3)
    source.setPixelColor(0, 0, QColor("#ff0000"))
    source.setPixelColor(1, 2, QColor("#0000ff"))
    state = TransformState.from_image(source)

    state.rotate_90_counterclockwise()

    assert state.image.size().width() == 3
    assert state.image.size().height() == 2
    assert state.image.pixelColor(2, 0) == QColor("#ff0000")
    assert state.image.pixelColor(0, 1) == QColor("#0000ff")
