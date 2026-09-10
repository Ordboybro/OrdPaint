import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ordpaint.ui.application_window import MainWindow
from ordpaint.ui.brush_presets import BrushPresetDock
from ordpaint.ui.color_lab import ColorLabDock
from ordpaint.ui.crash_reporter import install as install_crash_reporter
from ordpaint.ui.grid_enhancement import install as install_grid_enhancement
from ordpaint.ui.grid_ux import install as install_grid_ux
from ordpaint.ui.image_ops import install as install_image_ops
from ordpaint.ui.keyboard_polish import install as install_keyboard_polish
from ordpaint.ui.layer_groups import LayerGroupDock
from ordpaint.ui.layout_restore import install as install_layout_restore
from ordpaint.ui.polish import install as install_polish
from ordpaint.ui.pressure_input import install as install_pressure_input
from ordpaint.ui.recovery_polish import install as install_recovery_polish
from ordpaint.ui.resize_integration import install as install_resize
from ordpaint.ui.selection_advanced import install as install_selection_advanced
from ordpaint.ui.selection_clip import install as install_selection_clip
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

    window = MainWindow()
    install_grid_ux(window)
    install_polish(window)
    install_pressure_input()
    install_resize(window)
    install_transform(window)
    install_transform_advanced(window)
    install_selection_advanced(window)
    install_selection_clip()
    install_image_ops(window)
    install_keyboard_polish(window)
    install_recovery_polish(window)

    window.brush_presets_dock = BrushPresetDock(window)
    window.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, window.brush_presets_dock)
    window.color_lab_dock = ColorLabDock(window)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.color_lab_dock)
    window.layer_group_dock = LayerGroupDock(window)
    window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, window.layer_group_dock)

    install_layout_restore(window)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
