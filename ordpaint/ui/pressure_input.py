from __future__ import annotations

from PySide6.QtGui import QTabletEvent

from ordpaint.ui.canvas import Canvas


def install() -> None:
    """Add optional tablet-pressure input without affecting mouse workflows."""
    if getattr(Canvas, "_ordpaint_pressure_installed", False):
        return

    original_init = Canvas.__init__
    original_draw_segment = Canvas._draw_segment

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self.brush_pressure = 1.0
        self.pressure_enabled = True

    def draw_segment(self, start, end) -> None:
        if not getattr(self, "pressure_enabled", True) or self.tool.value not in {"brush", "eraser"}:
            original_draw_segment(self, start, end)
            return
        pressure = max(0.05, min(1.0, float(getattr(self, "brush_pressure", 1.0))))
        base_size = self.brush_size
        base_opacity = self.opacity
        self.brush_size = max(1, round(base_size * (0.35 + 0.65 * pressure)))
        self.opacity = max(1, round(base_opacity * (0.45 + 0.55 * pressure)))
        try:
            original_draw_segment(self, start, end)
        finally:
            self.brush_size = base_size
            self.opacity = base_opacity

    def tablet_event(self, event: QTabletEvent) -> None:
        point = self.widget_to_canvas(event.position())
        if point is None:
            event.ignore()
            return
        self.brush_pressure = max(0.05, min(1.0, float(event.pressure())))
        if event.type() in {QTabletEvent.Type.TabletPress, QTabletEvent.Type.TabletMove}:
            if self.tool.value in {"brush", "eraser"} and not self.document.active_layer.locked:
                if event.type() == QTabletEvent.Type.TabletPress:
                    self.action_started.emit()
                    self._drawing = True
                    self._last_canvas_pos = point
                    self._start_canvas_pos = point
                    self._draw_segment(point, point)
                elif self._drawing and self._last_canvas_pos is not None:
                    self._draw_segment(self._last_canvas_pos, point)
                    self._last_canvas_pos = point
                self.update()
                event.accept()
                return
        if event.type() == QTabletEvent.Type.TabletRelease:
            self._drawing = False
            self._last_canvas_pos = None
            self._start_canvas_pos = None
            self.brush_pressure = 1.0
            self.update()
            event.accept()
            return
        event.ignore()

    Canvas.__init__ = init
    Canvas._draw_segment = draw_segment
    Canvas.tabletEvent = tablet_event
    Canvas._ordpaint_pressure_installed = True
