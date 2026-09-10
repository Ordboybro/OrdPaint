from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtTest import QTest

from ordpaint.core.tools import Tool
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


def test_full_editor_startup_and_interaction(qapp, monkeypatch) -> None:
    monkeypatch.setattr("ordpaint.ui.application_window.SessionManager.recover_or_none", lambda self: None)

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
    qapp.processEvents()
    QTest.qWait(30)
    qapp.processEvents()

    screenshot = window.grab()
    assert screenshot.width() > 0
    assert screenshot.height() > 0
    assert window.devicePixelRatioF() >= 1.0
    screenshot_path = os.environ.get("ORDPAINT_SMOKE_SCREENSHOT")
    if screenshot_path:
        destination = Path(screenshot_path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert screenshot.save(str(destination), "PNG")

    window.canvas.fit_to_window()
    window.canvas.zoom_in()
    window.canvas.zoom_out()
    window.canvas.reset_view()
    window.canvas.set_show_grid(True)
    window.canvas.set_show_rulers(False)
    window.canvas.set_show_rulers(True)

    center = window.canvas.rect().center()
    window.canvas.set_tool(Tool.BRUSH)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=center)
    QTest.mouseMove(window.canvas, center + QPoint(20, 10), 20)
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=center + QPoint(20, 10))

    for tool in Tool:
        window.canvas.set_tool(tool)
        assert window.canvas.tool is tool

    window.canvas.select_all()
    assert window.canvas.begin_transform()
    assert window.canvas.rotate_transform_clockwise()
    assert window.canvas.flip_transform_horizontal()
    assert window.canvas.flip_transform_vertical()
    assert window.canvas.cancel_transform()

    window.close()
    qapp.processEvents()
