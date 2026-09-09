from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.polish import ColorStudio, install


def test_polish_installs_color_studio_and_brush_controls(qt_app) -> None:
    window = MainWindow()
    install(window)
    assert isinstance(window.color_studio, ColorStudio)
    assert window.grid_action.shortcut().toString() == "Ctrl+G"
    assert window.canvas.brush_hardness == 100
    assert window.canvas.brush_spacing == 20
    assert window.canvas.brush_smoothness == 0
    assert window.canvas.fill_tolerance == 0
    window.canvas.set_brush_hardness(60)
    window.canvas.set_brush_spacing(30)
    window.canvas.set_brush_smoothness(20)
    window.canvas.set_fill_tolerance(12)
    assert window.canvas.brush_hardness == 60
    assert window.canvas.brush_spacing == 30
    assert window.canvas.brush_smoothness == 20
    assert window.canvas.fill_tolerance == 12
    window.close()
