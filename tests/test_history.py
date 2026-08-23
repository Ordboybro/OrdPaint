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


def test_dirty_state_tracks_saved_position(qt_app):
    document = Document(10, 10)
    history = History()
    history.mark_saved()
    assert history.is_dirty() is False

    history.push(document)
    document.add_layer("Second")
    assert history.is_dirty() is True

    restored = history.undo(document)
    assert restored is not None
    assert history.is_dirty() is False

    redone = history.redo(restored)
    assert redone is not None
    assert history.is_dirty() is True


def test_branch_after_undo_stays_dirty(qt_app):
    document = Document(10, 10)
    history = History()
    history.mark_saved()

    history.push(document)
    document.add_layer("A")
    restored = history.undo(document)
    assert restored is not None

    history.push(restored)
    restored.add_layer("B")
    assert history.is_dirty() is True
    assert history.can_redo() is False


def test_history_limit():
    document = Document(8, 8)
    history = History(limit=2)
    for _ in range(5):
        history.push(document)
        document = document.copy()
    assert len(history) == 2
