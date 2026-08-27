from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(slots=True)
class UIState:
    """Serializable user-interface state independent from Qt's QSettings.

    Keeping this object Qt-free makes persistence easy to test and lets the UI
    layer store geometry/state with QSettings without leaking Qt types into the
    application core.
    """

    geometry: bytes | None = None
    window_state: bytes | None = None
    zoom: float = 1.0
    show_grid: bool = False
    show_rulers: bool = True
    grid_size: int = 32
    brush_size: int = 8
    opacity: int = 100
    color: str = "#111111"
    recent_paths: list[str] = field(default_factory=list)

    MIN_ZOOM = 0.05
    MAX_ZOOM = 16.0

    def normalize(self) -> None:
        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, float(self.zoom)))
        self.grid_size = max(2, min(2048, int(self.grid_size)))
        self.brush_size = max(1, min(500, int(self.brush_size)))
        self.opacity = max(1, min(100, int(self.opacity)))
        self.color = self._normalize_color(self.color)
        self.recent_paths = self._deduplicate_paths(self.recent_paths)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "UIState":
        state = cls(
            geometry=cls._as_bytes(data.get("geometry")),
            window_state=cls._as_bytes(data.get("window_state")),
            zoom=cls._as_float(data.get("zoom"), 1.0),
            show_grid=bool(data.get("show_grid", False)),
            show_rulers=bool(data.get("show_rulers", True)),
            grid_size=cls._as_int(data.get("grid_size"), 32),
            brush_size=cls._as_int(data.get("brush_size"), 8),
            opacity=cls._as_int(data.get("opacity"), 100),
            color=str(data.get("color", "#111111")),
            recent_paths=cls._as_paths(data.get("recent_paths")),
        )
        state.normalize()
        return state

    def to_mapping(self) -> dict[str, Any]:
        self.normalize()
        return {
            "geometry": self.geometry,
            "window_state": self.window_state,
            "zoom": self.zoom,
            "show_grid": self.show_grid,
            "show_rulers": self.show_rulers,
            "grid_size": self.grid_size,
            "brush_size": self.brush_size,
            "opacity": self.opacity,
            "color": self.color,
            "recent_paths": list(self.recent_paths),
        }

    @staticmethod
    def _as_bytes(value: Any) -> bytes | None:
        if value is None:
            return None
        if isinstance(value, bytes):
            return value
        try:
            return bytes(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_float(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_int(value: Any, default: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_paths(value: Any) -> list[str]:
        if isinstance(value, (str, bytes)) or value is None:
            return []
        try:
            return [str(path) for path in value if str(path).strip()]
        except TypeError:
            return []

    @staticmethod
    def _normalize_color(value: str) -> str:
        value = str(value).strip()
        if len(value) == 7 and value.startswith("#"):
            try:
                int(value[1:], 16)
            except ValueError:
                return "#111111"
            return value.lower()
        return "#111111"

    @staticmethod
    def _deduplicate_paths(paths: list[str]) -> list[str]:
        result: list[str] = []
        seen: set[str] = set()
        for path in paths:
            key = path.casefold()
            if key and key not in seen:
                seen.add(key)
                result.append(path)
        return result
