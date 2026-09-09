from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.polish import ColorStudio, install


def test_polish_installs_color_studio(qt_app) -> None:
    window = MainWindow()
    install(window)
    assert isinstance(window.color_studio, ColorStudio)
    assert window.grid_action.shortcut().toString() == "Ctrl+G"
    window.close()
