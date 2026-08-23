from ordpaint.core.document import Document
from ordpaint.core.history import History


def test_undo_redo_restores_document(qt_app):
    document = Document(10, 10)
    history = History(limit=2)
    history.push(document)

    document.add_layer("Second")
    restored = history.undo(document)
    assert restored is not None
    assert len(restored.layers) == 1

    redone = history.redo(restored)
    assert redone is not None
    assert len(redone.layers) == 2
