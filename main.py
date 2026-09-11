import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.brush_presets import BrushPresetDock
from ordpaint.ui.color_lab import ColorLabDock
from ordpaint.ui.crash_reporter import install as install_crash_reporter
from ordpaint.ui.final_polish import install as install_final_polish
from ordpaint.ui.grid_enhancement import install as install_grid_enhancement
from ordpaint.ui.grid_ux import install as install_grid_ux
from ordpaint.ui.keyboard_polish import install as install_keyboard_polish
from ordpaint.ui.layout_restore import install as install_layout_restore
from ordpaint.ui.polish import install as install_polish
from ordpaint.ui.pressure_input import install as install_pressure_input
from ordpaint.ui.recovery_polish import install as install_recovery_polish
from ordpaint.ui.resize_integration import install as install_resize
from ordpaint.ui.transform_advanced import install as install_transform_advanced
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
    install_grid_ux_class = install_grid_ux

    window = MainWindow()
    install_grid_ux_class(window)
    install_polish(window)
    install_pressure_input()
    install_resize(window)
    install_transform(window)
    install_transform_advanced(window)
    install_keyboard_polish(window)
    install_recovery_polish(window)

    window.brush_presets_dock = BrushPresetDock(window)
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, window.brush_presets_dock)
    window.color_lab_dock = ColorLabDock(window)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.color_lab_dock)

    install_layout_restore(window)
    install_final_polish(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
