from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.keyboard_polish import install


def test_keyboard_polish_adds_transform_and_view_shortcuts(qt_app) -> None:
    window = MainWindow()
    install(window)
    assert window.flip_horizontal_action.shortcut().toString() == "Ctrl+Shift+H"
    assert window.flip_vertical_action.shortcut().toString() == "Ctrl+Shift+V"
    assert window.rotate_clockwise_action.shortcut().toString() == "Ctrl+Shift+R"
    assert window.rotate_counterclockwise_action.shortcut().toString() == "Ctrl+Shift+L"
    assert window.reset_view_action.shortcut().toString() == "1"
    assert window.fit_view_action.shortcut().toString() == "2"
    window.close()
