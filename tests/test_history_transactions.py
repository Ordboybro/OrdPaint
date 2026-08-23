from ordpaint.core.document import Document
from ordpaint.core.history import History


def test_transaction_creates_one_undo_step(qt_app):
    document = Document(8, 8)
    history = History()
    assert history.begin_transaction(document)
    document.active_layer.name = "A"
    document.active_layer.name = "B"
    assert history.end_transaction(document)
    assert len(history) == 1
    restored = history.undo(document)
    assert restored is not None
    assert restored.active_layer.name == "Layer 1"


def test_unchanged_transaction_is_ignored(qt_app):
    document = Document(8, 8)
    history = History()
    history.begin_transaction(document)
    assert not history.end_transaction(document)
    assert len(history) == 0
