import sys

from PySide6.QtWidgets import QApplication

from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.brush_presets import BrushPresetDock
from ordpaint.ui.color_lab import ColorLabDock
from ordpaint.ui.crash_reporter import install as install_crash_reporter
from ordpaint.ui.grid_enhancement import install as install_grid_enhancement
from ordpaint.ui.keyboard_polish import install as install_keyboard_polish
from ordpaint.ui.layout_restore import install as install_layout_restore
from ordpaint.ui.polish import install as install_polish
from ordpaint.ui.resize_integration import install as install_resize
from ordpaint.ui.transform_integration import install as install_transform


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("OrdPaint")
    app.setApplicationDisplayName("OrdPaint")
    app.setOrganizationName("OrdStudio")
    app.setOrganizationDomain("ordpaint.local")
    app.setStyle("Fusion")
    install_crash_reporter()
    install_grid_enhancement()

    window = MainWindow()
    install_polish(window)
    install_resize(window)
    install_transform(window)
    install_keyboard_polish(window)

    window.brush_presets_dock = BrushPresetDock(window)
    window.addDockWidget(window.brush_presets_dock.allowedAreas() & window.brush_presets_dock.allowedAreas() or 1, window.brush_presets_dock)
    window.color_lab_dock = ColorLabDock(window)
    window.addDockWidget(window.color_lab_dock.allowedAreas() & window.color_lab_dock.allowedAreas() or 2, window.color_lab_dock)
    window.canvas.color_picked.connect(window.color_lab_dock._set_color)

    install_layout_restore(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
