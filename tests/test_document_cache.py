from PySide6.QtGui import QColor

from ordpaint.core.document import Document


def test_composite_cache_is_bounded() -> None:
    document = Document(16, 16)
    limit = document._COMPOSITE_CACHE_LIMIT

    for index in range(limit + 5):
        document.composite(QColor(index, index, index, 255))

    assert len(document._composite_cache) == limit


def test_composite_cache_is_invalidated_after_touch() -> None:
    document = Document(16, 16)
    document.composite(QColor("white"))
    assert document._composite_cache

    document.touch()

    assert not document._composite_cache


def test_composite_cache_refreshes_lru_order() -> None:
    document = Document(16, 16)
    first = QColor("red")
    second = QColor("blue")
    document.composite(first)
    document.composite(second)
    document.composite(first)

    keys = list(document._composite_cache)
    assert keys[-1] == (first.red(), first.green(), first.blue(), first.alpha())
