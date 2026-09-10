from __future__ import annotations

from PySide6.QtCore import QEvent, QPointF
from PySide6.QtGui import QTabletEvent

from ordpaint.core.brush_engine import BrushDynamics, BrushEngine, Stabilizer
from ordpaint.ui.canvas import Canvas


def install() -> None:
    """Route mouse/tablet brush parameters through the shared BrushEngine."""
    if getattr(Canvas, "_ordpaint_pressure_installed", False):
        return

    original_init = Canvas.__init__
    original_draw_segment = Canvas._draw_segment

    def init(self, *args, **kwargs) -> None:
        original_init(self, *args, **kwargs)
        self.brush_pressure = 1.0
        self.pressure_enabled = True
        self.brush_engine = BrushEngine()
        self.brush_engine.preset.dynamics = BrushDynamics()
        self.brush_engine.preset.stabilizer = Stabilizer()

    def draw_segment(self, start, end) -> None:
        if not getattr(self, "pressure_enabled", True) or self.tool.value not in {"brush", "eraser"}:
            original_draw_segment(self, start, end)
            return
        pressure = max(0.0, min(1.0, float(getattr(self, "brush_pressure", 1.0))))
        engine = self.brush_engine
        if self._last_canvas_pos is None or start == end:
            engine.begin_stroke(QPointF(start))
        smoothed_end = engine.point(QPointF(end), pressure)
        base_size = self.brush_size
        base_opacity = self.opacity
        size, opacity = engine.preset.dynamics.apply(base_size, base_opacity, pressure)
        self.brush_size = max(1, round(size))
        self.opacity = max(1, round(opacity))
        try:
            original_draw_segment(start, smoothed_end.toPoint())
        finally:
            self.brush_size = base_size
            self.opacity = base_opacity

    def tablet_event(self, event: QTabletEvent) -> None:
        point = self.widget_to_canvas(event.position())
        if point is None:
            event.ignore()
            return
        self.brush_pressure = max(0.0, min(1.0, float(event.pressure())))
        press = QEvent.Type.TabletPress
        move = QEvent.Type.TabletMove
        release = QEvent.Type.TabletRelease
        if event.type() in {press, move} and self.tool.value in {"brush", "eraser"} and not self.document.active_layer.locked:
            if event.type() == press:
                self.action_started.emit()
                self._drawing = True
                self._last_canvas_pos = None
                self._start_canvas_pos = point
                self._draw_segment(point, point)
                self._last_canvas_pos = point
            elif self._drawing:
                self._draw_segment(self._last_canvas_pos or point, point)
                self._last_canvas_pos = point
            self.update()
            event.accept()
            return
        if event.type() == release:
            self._drawing = False
            self._last_canvas_pos = None
            self._start_canvas_pos = None
            self.brush_pressure = 1.0
            self.brush_engine.end_stroke()
            self.update()
            event.accept()
            return
        event.ignore()

    Canvas.__init__ = init
    Canvas._draw_segment = draw_segment
    Canvas.tabletEvent = tablet_event
    Canvas._ordpaint_pressure_installed = True
