from __future__ import annotations

from dataclasses import dataclass, field
from math import hypot

from PySide6.QtCore import QPointF


@dataclass(frozen=True)
class BrushDynamics:
    """Pressure response for size and opacity."""

    size_pressure: float = 0.65
    opacity_pressure: float = 0.55
    minimum_pressure: float = 0.05
    minimum_size_factor: float = 0.35
    minimum_opacity_factor: float = 0.45

    def apply(self, size: float, opacity: float, pressure: float) -> tuple[float, float]:
        p = max(self.minimum_pressure, min(1.0, float(pressure)))
        size_factor = self.minimum_size_factor + self.size_pressure * p
        opacity_factor = self.minimum_opacity_factor + self.opacity_pressure * p
        return max(0.1, size * size_factor), max(0.01, opacity * opacity_factor)


@dataclass(frozen=True)
class Stabilizer:
    """Exponential pointer smoothing; strength 0 disables stabilization."""

    strength: float = 0.0

    def smooth(self, previous: QPointF | None, current: QPointF) -> QPointF:
        if previous is None:
            return QPointF(current)
        strength = max(0.0, min(0.95, float(self.strength)))
        if strength <= 0:
            return QPointF(current)
        return QPointF(
            previous.x() * strength + current.x() * (1.0 - strength),
            previous.y() * strength + current.y() * (1.0 - strength),
        )


@dataclass
class BrushPreset:
    name: str
    size: int = 8
    opacity: int = 100
    hardness: int = 100
    spacing: int = 12
    smoothing: int = 0
    dynamics: BrushDynamics = field(default_factory=BrushDynamics)
    stabilizer: Stabilizer = field(default_factory=Stabilizer)


class BrushEngine:
    """UI-independent brush parameter engine used by mouse and tablet input."""

    def __init__(self) -> None:
        self.preset = BrushPreset("Basic")
        self.pressure = 1.0
        self._smoothed: QPointF | None = None

    def begin_stroke(self, point: QPointF) -> QPointF:
        self._smoothed = QPointF(point)
        return QPointF(point)

    def point(self, point: QPointF, pressure: float = 1.0) -> QPointF:
        self.pressure = max(0.0, min(1.0, float(pressure)))
        self._smoothed = self.preset.stabilizer.smooth(self._smoothed, point)
        return QPointF(self._smoothed)

    def end_stroke(self) -> None:
        self._smoothed = None
        self.pressure = 1.0

    def effective_size_opacity(self, pressure: float | None = None) -> tuple[float, float]:
        return self.preset.dynamics.apply(
            self.preset.size,
            self.preset.opacity,
            self.pressure if pressure is None else pressure,
        )

    def stamp_count(self, distance: float) -> int:
        spacing = max(1, min(1000, int(self.preset.spacing))) / 100.0
        diameter = max(1.0, float(self.preset.size))
        return max(1, int(hypot(distance, 0) / max(1.0, diameter * spacing)) + 1)

    def preview_points(self, start: QPointF, end: QPointF, pressure: float = 1.0) -> list[tuple[QPointF, float]]:
        distance = hypot(end.x() - start.x(), end.y() - start.y())
        count = self.stamp_count(distance)
        size, _ = self.effective_size_opacity(pressure)
        if count == 1:
            return [(QPointF(start), size)]
        return [
            (
                QPointF(start.x() + (end.x() - start.x()) * i / (count - 1), start.y() + (end.y() - start.y()) * i / (count - 1)),
                size,
            )
            for i in range(count)
        ]
